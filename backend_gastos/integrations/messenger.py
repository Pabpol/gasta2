"""
Telegram integration for interactive expense categorization and sharing decisions.
Handles bot communication, inline keyboards, and user responses.
"""
import asyncio
import httpx
import logging
from typing import Dict, List, Any, Optional
import json
import re

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.paths import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

class TelegramMessenger:
    """Telegram bot integration for expense management"""
    
    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram configuration missing. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
    
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
        """Send request to Telegram API"""
        if not self.bot_token:
            logger.warning("No Telegram bot token configured")
            return None
        
        url = f"{self.base_url}/{method}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Telegram API error: {e}")
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
        
        result = await self._send_request("sendMessage", data)
        if result and result.get('ok'):
            return result['result']['message_id']
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

async def handle_telegram_update(update: Dict[str, Any], storage, categorizer):
    """
    Handle incoming Telegram updates (callbacks and messages).
    Processes category selection, sharing decisions, and text commands.
    """
    messenger = TelegramMessenger()
    
    try:
        # Handle callback queries (button presses)
        if 'callback_query' in update:
            callback = update['callback_query']
            data = callback.get('data', '')
            message_id = callback['message']['message_id']
            
            if data.startswith('cat:'):
                # Category selection: cat:<gid>:<categoria>
                _, gasto_id, categoria = data.split(':', 2)
                
                # Update expense with category
                gasto = storage.get(gasto_id)
                if gasto:
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
            
            # Handle sharing commands: "id <gid> con <Nombre> [% <porcentaje>]"
            if text.startswith('id '):
                await _handle_sharing_command(text, storage, messenger)
    
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

# Instantiate global messenger for easy access
messenger = TelegramMessenger()
