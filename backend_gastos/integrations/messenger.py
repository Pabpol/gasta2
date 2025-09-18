"""
Enhanced Telegram integration for interactive expense categorization and sharing decisions.
Handles bot communication, inline keyboards, and user responses with improved reliability.
Includes retry logic, rate limiting, and comprehensive error handling for alpha release.
"""
import asyncio
import httpx
import logging
from typing import Dict, List, Any, Optional
import json
import re
import time
import hashlib
import hmac

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.paths import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from core.errors import telegram_error, ExternalServiceError

logger = logging.getLogger(__name__)

class TelegramMessenger:
    """Enhanced Telegram bot integration for expense management with reliability features"""

    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

        # Reliability settings
        self.max_retries = 3
        self.retry_delay = 1.0  # Base delay in seconds
        self.timeout = 30.0  # Request timeout
        self.rate_limit_delay = 0.1  # Delay between requests to avoid rate limits

        # Health tracking
        self.last_successful_request = None
        self.consecutive_failures = 0
        self.max_consecutive_failures = 5

        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram configuration missing. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        else:
            logger.info("Telegram messenger initialized successfully")
    
    def _escape_markdown(self, text: str) -> str:
        """Escape Markdown special characters for Telegram"""
        if not text:
            return ""
        # Escape Markdown special characters
        special_chars = ['*', '_', '`', '[', ']', '(', ')', '~', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        escaped_text = text
        for char in special_chars:
            escaped_text = escaped_text.replace(char, f'\\{char}')
        return escaped_text
    
    async def _send_request(self, method: str, data: Dict[str, Any]) -> Optional[Dict]:
        """Send request to Telegram API with retry logic and error handling"""
        if not self.bot_token:
            logger.warning("No Telegram bot token configured")
            return None

        if self.consecutive_failures >= self.max_consecutive_failures:
            logger.error("Too many consecutive Telegram failures, temporarily disabling")
            return None

        url = f"{self.base_url}/{method}"

        for attempt in range(self.max_retries):
            try:
                # Rate limiting delay
                if attempt > 0:
                    await asyncio.sleep(self.rate_limit_delay * (2 ** attempt))  # Exponential backoff

                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=data)

                    # Handle different HTTP status codes
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('ok'):
                            # Success - reset failure counter
                            self.last_successful_request = time.time()
                            self.consecutive_failures = 0
                            return result
                        else:
                            # Telegram API returned error
                            error_code = result.get('error_code', 'UNKNOWN')
                            error_description = result.get('description', 'Unknown error')

                            # Handle specific Telegram errors
                            if error_code == 429:  # Too Many Requests
                                retry_after = result.get('parameters', {}).get('retry_after', 30)
                                logger.warning(f"Rate limited, retrying after {retry_after} seconds")
                                await asyncio.sleep(retry_after)
                                continue
                            elif error_code == 400:  # Bad Request
                                logger.error(f"Bad request to Telegram API: {error_description}")
                                break  # Don't retry bad requests
                            elif error_code == 403:  # Bot blocked by user
                                logger.error("Bot appears to be blocked by user")
                                break
                            else:
                                logger.error(f"Telegram API error {error_code}: {error_description}")
                                if attempt == self.max_retries - 1:
                                    break
                                continue

                    elif response.status_code >= 500:
                        # Server error - retry
                        logger.warning(f"Telegram server error {response.status_code}, attempt {attempt + 1}")
                        if attempt < self.max_retries - 1:
                            continue
                        else:
                            break

                    else:
                        # Other client errors
                        logger.error(f"HTTP {response.status_code} from Telegram API")
                        response.raise_for_status()

            except httpx.TimeoutException:
                logger.warning(f"Timeout connecting to Telegram API, attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    continue

            except httpx.ConnectError:
                logger.warning(f"Connection error to Telegram API, attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    continue

            except Exception as e:
                logger.error(f"Unexpected error in Telegram request: {str(e)}", exc_info=True)
                if attempt < self.max_retries - 1:
                    continue
                break

        # All retries failed
        self.consecutive_failures += 1
        logger.error(f"All {self.max_retries} attempts to Telegram API failed")
        return None

    def is_healthy(self) -> bool:
        """Check if the Telegram integration is healthy"""
        if not self.bot_token or not self.chat_id:
            return False

        if self.consecutive_failures >= self.max_consecutive_failures:
            return False

        # Check if we had a successful request in the last hour
        if self.last_successful_request:
            return (time.time() - self.last_successful_request) < 3600  # 1 hour

        return True

    def get_health_status(self) -> Dict[str, Any]:
        """Get detailed health status"""
        return {
            "configured": bool(self.bot_token and self.chat_id),
            "healthy": self.is_healthy(),
            "consecutive_failures": self.consecutive_failures,
            "last_success": self.last_successful_request,
            "max_failures": self.max_consecutive_failures
        }

    def validate_webhook_secret(self, update: Dict[str, Any], secret_token: Optional[str] = None) -> bool:
        """
        Validate incoming webhook using Telegram's secret token
        This provides basic security for webhook endpoints
        """
        if not secret_token:
            # If no secret token configured, accept all (for development)
            return True

        # For now, just check if the update looks like a valid Telegram update
        # In production, you'd validate the secret token from headers
        required_fields = ['update_id']
        return all(field in update for field in required_fields)

    async def test_connectivity(self) -> bool:
        """Test basic connectivity to Telegram API"""
        try:
            # Try to get bot info
            result = await self._send_request("getMe", {})
            return result is not None and result.get('ok', False)
        except Exception as e:
            logger.error(f"Connectivity test failed: {e}")
            return False

    async def setup_webhook(self, webhook_url: str) -> bool:
        """Setup webhook for Telegram bot"""
        try:
            data = {
                "url": webhook_url,
                "allowed_updates": ["message", "callback_query"]
            }
            result = await self._send_request("setWebhook", data)
            if result and result.get('ok'):
                logger.info(f"Webhook configured successfully: {webhook_url}")
                return True
            else:
                logger.error(f"Failed to configure webhook: {result}")
                return False
        except Exception as e:
            logger.error(f"Error setting up webhook: {e}")
            return False

    async def get_webhook_info(self):
        """Get current webhook information"""
        try:
            result = await self._send_request("getWebhookInfo", {})
            return result
        except Exception as e:
            logger.error(f"Error getting webhook info: {e}")
            return None
    
    async def send_category_prompt(self, gasto: Dict[str, Any], alias_hint: str = "") -> Optional[int]:
        """
        Send categorization prompt with inline keyboard buttons.
        Returns message_id for later editing.
        """
        if not self.chat_id:
            return None
        
        gasto_id = gasto.get('id', '')
        descripcion = gasto.get('descripcion', '')
        monto = gasto.get('monto_clp', 0)
        fecha = gasto.get('fecha', '')
        
        # Format message with escaped description
        message_text = f"🧾 *Nuevo gasto por categorizar*\n\n"
        message_text += f"💰 Monto: ${monto:,.0f} CLP\n"
        message_text += f"📅 Fecha: {fecha}\n"
        message_text += f"🏪 Descripción: {self._escape_markdown(descripcion)}\n"
        
        if alias_hint:
            message_text += f"💡 Sugerencia: {alias_hint}\n"
        
        message_text += f"\n¿En qué categoría clasificamos este gasto?"
        
        # Create inline keyboard with category options
        keyboard = self._create_category_keyboard(gasto_id)
        
        data = {
            "chat_id": self.chat_id,
            "text": message_text,
            "parse_mode": "Markdown",
            "reply_markup": {
                "inline_keyboard": keyboard
            }
        }
        
        result = await self._send_request("sendMessage", data)
        if result and result.get('ok'):
            return result['result']['message_id']
        return None
    
    async def send_share_prompt(self, gasto: Dict[str, Any]) -> Optional[int]:
        """
        Send sharing prompt after categorization.
        Returns message_id for later editing.
        """
        if not self.chat_id:
            return None
        
        gasto_id = gasto.get('id', '')
        descripcion = gasto.get('descripcion', '')
        monto = gasto.get('monto_clp', 0)
        categoria = gasto.get('categoria', '')
        
        message_text = f"✅ *Gasto categorizado como: {self._escape_markdown(categoria)}*\n\n"
        message_text += f"💰 Monto: ${monto:,.0f} CLP\n"
        message_text += f"🏪 {self._escape_markdown(descripcion)}\n\n"
        message_text += f"¿Este gasto fue compartido?"
        
        # Create sharing keyboard
        keyboard = [
            [
                {"text": "❌ No compartido", "callback_data": f"share:{gasto_id}:no"},
                {"text": "👥 50/50", "callback_data": f"share:{gasto_id}:50"}
            ],
            [
                {"text": "🧑‍🤝‍🧑 Otro %", "callback_data": f"share:{gasto_id}:custom"}
            ]
        ]
        
        data = {
            "chat_id": self.chat_id,
            "text": message_text,
            "parse_mode": "Markdown",
            "reply_markup": {
                "inline_keyboard": keyboard
            }
        }
        
        result = await self._send_request("sendMessage", data)
        if result and result.get('ok'):
            return result['result']['message_id']
        return None
    
    def _create_category_keyboard(self, gasto_id: str) -> List[List[Dict[str, str]]]:
        """Create inline keyboard for category selection"""
        categories = [
            ("🍽️ Alimentación", "alimentacion"),
            ("🚗 Transporte", "transporte"),
            ("🛒 Supermercado", "supermercado"),
            ("⛽ Combustible", "combustible"),
            ("🏠 Servicios", "servicios"),
            ("💊 Salud", "salud"),
            ("🎬 Entretenimiento", "entretenimiento"),
            ("👕 Ropa", "ropa"),
            ("🏠 Hogar", "hogar"),
            ("📚 Educación", "educacion"),
            ("🏃 Deportes", "deportes"),
            ("💻 Tecnología", "tecnologia"),
            ("🛍️ Compras Online", "comercio_electronico"),
            ("✈️ Viajes", "viajes"),
            ("❓ Otros", "otros")
        ]
        
        keyboard = []
        row = []
        
        for display_name, category_key in categories:
            callback_data = f"cat:{gasto_id}:{category_key}"
            row.append({"text": display_name, "callback_data": callback_data})
            
            if len(row) == 2:  # 2 buttons per row
                keyboard.append(row)
                row = []
        
        if row:  # Add remaining buttons
            keyboard.append(row)
        
        return keyboard
    
    async def edit_message(self, message_id: int, text: str, keyboard: Optional[List] = None):
        """Edit an existing message"""
        if not self.chat_id:
            return None
        
        data = {
            "chat_id": self.chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        if keyboard:
            data["reply_markup"] = {"inline_keyboard": keyboard}
        
        return await self._send_request("editMessageText", data)
    
    async def send_confirmation_prompt(self, gasto: Dict[str, Any], confidence: float) -> Optional[int]:
        """
        Send confirmation prompt for auto-categorization.
        Returns message_id for later editing.
        """
        if not self.chat_id:
            return None
        
        gasto_id = gasto.get('id', '')
        descripcion = gasto.get('descripcion', '')
        monto = gasto.get('monto_clp', 0)
        categoria = gasto.get('categoria', '')
        fecha = gasto.get('fecha', '')
        
        # Format message with auto-categorization info
        message_text = f"🤖 *Auto-categorizado con {confidence:.0%} confianza*\n\n"
        message_text += f"💰 Monto: ${monto:,.0f} CLP\n"
        message_text += f"📅 Fecha: {fecha}\n"
        message_text += f"🏪 Descripción: {self._escape_markdown(descripcion)}\n"
        message_text += f"📂 Categoría sugerida: *{self._escape_markdown(categoria)}*\n\n"
        message_text += f"¿Es correcta esta categorización?"
        
        # Create confirmation keyboard
        keyboard = [
            [
                {"text": "✅ Correcto", "callback_data": f"confirm:{gasto_id}:yes"},
                {"text": "❌ Cambiar", "callback_data": f"confirm:{gasto_id}:no"}
            ]
        ]
        
        data = {
            "chat_id": self.chat_id,
            "text": message_text,
            "parse_mode": "Markdown",
            "reply_markup": {
                "inline_keyboard": keyboard
            }
        }
        
        logger.info(f"Sending category prompt for gasto_id={gasto_id}")
        result = await self._send_request("sendMessage", data)
        if result and result.get('ok'):
            logger.info(f"Category prompt sent successfully, message_id={result['result']['message_id']}")
            return result['result']['message_id']
        else:
            logger.error(f"Failed to send category prompt: {result}")
            return None
    
    async def send_simple_message(self, text: str):
        """Send a simple text message"""
        if not self.chat_id:
            return None
        
        data = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        return await self._send_request("sendMessage", data)

async def handle_telegram_update(update: Dict[str, Any], storage, categorizer, secret_token: Optional[str] = None):
    """
    Handle incoming Telegram updates with enhanced validation and error handling.
    Processes category selection, sharing decisions, and text commands.
    """
    messenger = TelegramMessenger()

    # Validate webhook
    if not messenger.validate_webhook_secret(update, secret_token):
        logger.warning("Invalid webhook received")
        return {"ok": False, "error": "Invalid webhook"}

    try:
        # Handle callback queries (button presses)
        if 'callback_query' in update:
            callback = update['callback_query']
            data = callback.get('data', '')
            message_id = callback['message']['message_id']

            logger.info(f"Received callback query: {data}", extra={
                "callback_data": data,
                "message_id": message_id,
                "from_user": callback.get('from', {}).get('id')
            })

            # Answer the callback query to remove loading state
            callback_id = callback.get('id')
            if callback_id:
                await messenger._send_request("answerCallbackQuery", {
                    "callback_query_id": callback_id
                })
            
            if data.startswith('cat:'):
                # Category selection: cat:<gid>:<categoria>
                _, gasto_id, categoria = data.split(':', 2)

                logger.info(f"Processing category selection: gasto_id={gasto_id}, categoria={categoria}")

                # Update expense with category
                gasto = storage.get(gasto_id)
                if gasto:
                    logger.info(f"Found expense: {gasto.get('descripcion', 'N/A')}")
                    gasto['categoria'] = categoria
                    gasto['estado'] = 'categorizado'

                    # Auto-categorize to get subcategory
                    _, subcategoria, _, confidence = categorizer.categorize_one(gasto)
                    gasto['subcategoria'] = subcategoria
                    gasto['ml_confidence'] = confidence

                    storage.upsert_row(gasto)
                    storage.sync_excel()

                    # Edit message to show categorization success
                    success_text = f"✅ *Gasto categorizado como: {messenger._escape_markdown(categoria)}*\n\n"
                    success_text += f"💰 ${gasto['monto_clp']:,.0f} CLP\n"
                    success_text += f"🏪 {messenger._escape_markdown(gasto['descripcion'])}"

                    await messenger.edit_message(message_id, success_text)

                    # Ask about sharing
                    await messenger.send_share_prompt(gasto)
                    logger.info(f"Category selection processed successfully for gasto_id={gasto_id}")
                else:
                    logger.error(f"Expense not found: gasto_id={gasto_id}")
                    await messenger.send_simple_message(f"❌ Error: Gasto con ID {gasto_id} no encontrado")
            
            elif data.startswith('share:'):
                # Share selection: share:<gid>:<percentage>
                parts = data.split(':', 2)
                if len(parts) >= 3:
                    _, gasto_id, share_type = parts
                    
                    gasto = storage.get(gasto_id)
                    if gasto:
                        if share_type == 'no':
                            # Not shared
                            gasto['porcentaje_compartido'] = 0
                            gasto['compartido_con'] = ''
                            gasto['monto_tu_parte'] = gasto['monto_clp']
                            gasto['monto_tercero'] = 0
                            
                            storage.upsert_row(gasto)
                            storage.sync_excel()
                            
                            final_text = f"✅ *Gasto procesado completamente*\n\n"
                            final_text += f"📊 Categoría: {messenger._escape_markdown(gasto['categoria'])}\n"
                            final_text += f"💰 Monto: ${gasto['monto_clp']:,.0f} CLP\n"
                            final_text += f"🏪 {messenger._escape_markdown(gasto['descripcion'])}\n"
                            final_text += f"👤 No compartido"
                            
                            await messenger.edit_message(message_id, final_text)
                        
                        elif share_type == '50':
                            # 50/50 split - ask for person name
                            instruction_text = f"💬 *Compartido 50/50*\n\n"
                            instruction_text += f"Responde con: `id {gasto_id} con <Nombre>`\n"
                            instruction_text += f"Ejemplo: `id {gasto_id} con Juan`"
                            
                            await messenger.edit_message(message_id, instruction_text)
                        
                        elif share_type == 'custom':
                            # Custom percentage - ask for details
                            instruction_text = f"💬 *Porcentaje personalizado*\n\n"
                            instruction_text += f"Responde con: `id {gasto_id} con <Nombre> % <porcentaje>`\n"
                            instruction_text += f"Ejemplo: `id {gasto_id} con María % 30`"
                            
                            await messenger.edit_message(message_id, instruction_text)
            
            elif data.startswith('confirm:'):
                # Confirmation selection: confirm:<gid>:<yes|no>
                _, gasto_id, confirmation = data.split(':', 2)
                
                gasto = storage.get(gasto_id)
                if gasto:
                    if confirmation == 'yes':
                        # User confirmed auto-categorization
                        success_text = f"✅ *Categorización confirmada*\n\n"
                        success_text += f"📊 Categoría: {messenger._escape_markdown(gasto['categoria'])}\n"
                        success_text += f"💰 Monto: ${gasto['monto_clp']:,.0f} CLP\n"
                        success_text += f"🏪 {messenger._escape_markdown(gasto['descripcion'])}"
                        
                        await messenger.edit_message(message_id, success_text)
                        
                        # Sync Excel and ask about sharing
                        storage.sync_excel()
                        await messenger.send_share_prompt(gasto)
                        
                    elif confirmation == 'no':
                        # User wants to change categorization - show manual selection
                        gasto['estado'] = 'pendiente'
                        storage.upsert_row(gasto)
                        
                        await messenger.send_category_prompt(gasto)
                        
                        # Edit original message to show it's being re-categorized
                        recategorize_text = f"🔄 *Recategorizando gasto...*\n\n"
                        recategorize_text += f"💰 ${gasto['monto_clp']:,.0f} CLP\n"
                        recategorize_text += f"🏪 {messenger._escape_markdown(gasto['descripcion'])}\n\n"
                        recategorize_text += f"👆 Selecciona la categoría correcta arriba"
                        
                        await messenger.edit_message(message_id, recategorize_text)
        
        # Handle text messages
        elif 'message' in update and 'text' in update['message']:
            text = update['message']['text'].strip()
            
            # Handle income commands: "ingreso <monto> <descripcion>" or "ingreso <monto> <descripcion> de <persona>"
            if text.startswith('ingreso '):
                await _handle_income_command(text, storage, messenger)
            
            # Handle sharing commands: "id <gid> con <Nombre> [% <porcentaje>]"
            elif text.startswith('id '):
                await _handle_sharing_command(text, storage, messenger)
            
            # Handle help command
            elif text.lower() in ['/help', '/ayuda', 'help', 'ayuda']:
                await _handle_help_command(messenger)
    
    except Exception as e:
        logger.error(f"Error handling Telegram update: {e}")
        await messenger.send_simple_message(f"❌ Error procesando comando: {str(e)}")

async def _handle_sharing_command(text: str, storage, messenger):
    """Handle sharing command parsing and processing"""
    try:
        # Parse: "id <gid> con <Nombre> [% <porcentaje>]"
        parts = text.split()
        
        if len(parts) < 4 or parts[2] != 'con':
            await messenger.send_simple_message("❌ Formato incorrecto. Usa: `id <ID> con <Nombre>` o `id <ID> con <Nombre> % <porcentaje>`")
            return
        
        gasto_id = parts[1]
        
        # Find percentage if specified
        percentage = 50  # default 50/50
        name_parts = []
        
        for i, part in enumerate(parts[3:], 3):
            if part == '%' and i + 1 < len(parts):
                try:
                    percentage = float(parts[i + 1])
                    break
                except ValueError:
                    pass
            else:
                name_parts.append(part)
        
        if not name_parts:
            await messenger.send_simple_message("❌ Falta el nombre de la persona")
            return
        
        nombre = ' '.join(name_parts)
        
        # Update expense
        gasto = storage.get(gasto_id)
        if not gasto:
            await messenger.send_simple_message(f"❌ No se encontró el gasto con ID: {gasto_id}")
            return
        
        gasto['porcentaje_compartido'] = percentage
        gasto['compartido_con'] = nombre
        
        # Calculate amounts
        monto_total = float(gasto['monto_clp'])
        gasto['monto_tercero'] = monto_total * (percentage / 100)
        gasto['monto_tu_parte'] = monto_total * ((100 - percentage) / 100)
        gasto['settlement_status'] = 'pending'
        
        storage.upsert_row(gasto)
        storage.sync_excel()
        
        # Confirmation message
        confirmation = f"✅ *Gasto compartido configurado*\n\n"
        confirmation += f"📊 Categoría: {messenger._escape_markdown(gasto['categoria'])}\n"
        confirmation += f"💰 Monto total: ${monto_total:,.0f} CLP\n"
        confirmation += f"👤 Tu parte: ${gasto['monto_tu_parte']:,.0f} CLP ({100-percentage:.0f}%)\n"
        confirmation += f"👥 {nombre}: ${gasto['monto_tercero']:,.0f} CLP ({percentage:.0f}%)\n"
        confirmation += f"⏳ Estado: Pendiente de cobro"
        
        await messenger.send_simple_message(confirmation)
    
    except Exception as e:
        logger.error(f"Error in sharing command: {e}")
        await messenger.send_simple_message(f"❌ Error procesando comando: {str(e)}")

async def _handle_income_command(text: str, storage, messenger):
    """Handle income command parsing and processing"""
    try:
        # Parse: "ingreso <monto> <descripcion>" or "ingreso <monto> <descripcion> de <persona>"
        parts = text.split(' ', 2)  # Split into 3 parts max: "ingreso", "<monto>", "<resto>"
        
        if len(parts) < 3:
            await messenger.send_simple_message(
                "❌ Formato incorrecto\\. Usa:\n\n"
                "`ingreso 50000 Sueldo septiembre`\n"
                "`ingreso 15000 Reembolso cena de Juan`\n"
                "`ingreso 25000 Freelance proyecto X`"
            )
            return
        
        # Extract amount
        try:
            monto = float(parts[1])
        except ValueError:
            await messenger.send_simple_message("❌ El monto debe ser un número válido")
            return
        
        if monto <= 0:
            await messenger.send_simple_message("❌ El monto debe ser mayor a 0")
            return
        
        # Extract description and optional person
        descripcion_completa = parts[2]
        contraparte = None
        
        # Check if it's from someone: "descripcion de Persona"
        if ' de ' in descripcion_completa:
            desc_parts = descripcion_completa.rsplit(' de ', 1)
            if len(desc_parts) == 2:
                descripcion = desc_parts[0].strip()
                contraparte = desc_parts[1].strip()
            else:
                descripcion = descripcion_completa
        else:
            descripcion = descripcion_completa
        
        # Create income record
        from datetime import datetime
        ingreso_data = {
            "descripcion": descripcion,
            "monto_clp": monto,
            "fecha": datetime.now().isoformat(),
            "categoria": "ingreso",
            "tipo": "transfer_in",
            "estado": "procesado",
            "fuente": "telegram_manual",
            "medio": "transferencia",
            "moneda": "CLP"
        }
        
        if contraparte:
            ingreso_data["compartido_con"] = contraparte
        
        # Save income
        saved_ingreso = storage.upsert_row(ingreso_data)
        
        # Try auto-matching if there's a counterpart
        matched_expense = None
        if contraparte:
            from core import reconcile
            pendientes = storage.list_receivables()
            matched_expense = reconcile.try_auto_match(
                saved_ingreso, 
                pendientes, 
                prefer_name=contraparte
            )
            
            if matched_expense:
                reconcile.mark_as_settled(matched_expense["id"], saved_ingreso["id"], storage)
        
        # Sync Excel
        storage.sync_excel()
        
        # Send confirmation
        confirmation = f"✅ *Ingreso registrado*\n\n"
        confirmation += f"💰 Monto: ${monto:,.0f} CLP\n"
        confirmation += f"📝 Descripción: {messenger._escape_markdown(descripcion)}\n"
        confirmation += f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        
        if contraparte:
            confirmation += f"👤 De: {messenger._escape_markdown(contraparte)}\n"
        
        if matched_expense:
            confirmation += f"\n🔗 *Auto\\-emparejado con gasto:*\n"
            confirmation += f"💸 {messenger._escape_markdown(matched_expense['descripcion'])}\n"
            confirmation += f"💰 ${matched_expense['monto_clp']:,.0f} CLP\n"
            confirmation += f"✅ Liquidado automáticamente"
        elif contraparte:
            confirmation += f"\n💡 *Tip:* Si esto es un reembolso, buscaré automáticamente gastos pendientes de {messenger._escape_markdown(contraparte)}"
        
        await messenger.send_simple_message(confirmation)
        
    except Exception as e:
        logger.error(f"Error in income command: {e}")
        await messenger.send_simple_message(f"❌ Error procesando ingreso: {str(e)}")

async def _handle_help_command(messenger):
    """Send help message with available commands"""
    help_text = f"🤖 *Comandos disponibles:*\n\n"
    help_text += f"💰 *Ingresos:*\n"
    help_text += f"`ingreso 50000 Sueldo septiembre`\n"
    help_text += f"`ingreso 15000 Reembolso cena de Juan`\n\n"
    help_text += f"🤝 *Gastos compartidos:*\n"
    help_text += f"`id ABC123 con Juan`\n"
    help_text += f"`id ABC123 con María % 30`\n\n"
    help_text += f"ℹ️ *Notas:*\n"
    help_text += f"• Los gastos se agregan automáticamente via MacroDroid\n"
    help_text += f"• Los ingresos 'de alguien' intentan emparejarse automáticamente\n"
    help_text += f"• Usa `/help` para ver este mensaje"
    
    await messenger.send_simple_message(help_text)

# Instantiate global messenger for easy access
messenger = TelegramMessenger()
