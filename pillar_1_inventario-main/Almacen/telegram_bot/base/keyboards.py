"""
Teclados inline para el bot de Telegram.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class Keyboards:
    """Clase con todos los teclados inline del bot."""
    
    @classmethod
    async def menu_principal(cls, es_supervisor=False, es_directivo=False):
        """
        Teclado del menú principal con opciones según el rol del usuario.
        
        Args:
            es_supervisor: Si el usuario es supervisor
            es_directivo: Si el usuario es directivo
        """
        keyboard = [
            [
                InlineKeyboardButton("📝 Nueva Requisición", callback_data="nueva_req"),
                InlineKeyboardButton("📋 Mis Requisiciones", callback_data="mis_req"),
            ]
        ]
        
        # Opciones solo para supervisores/directivos
        if es_supervisor or es_directivo:
            keyboard.append([
                InlineKeyboardButton("👨‍💼 Aprobaciones Pendientes", callback_data="pendientes_aprobacion")
            ])
        
        # Opciones solo para directivos
        if es_directivo:
            keyboard.append([
                InlineKeyboardButton("📊 Reportes", callback_data="reportes"),
                InlineKeyboardButton("⚙️ Administración", callback_data="admin")
            ])
        
        # Opción de ayuda siempre visible
        keyboard.append([
            InlineKeyboardButton("❓ Ayuda", callback_data="help")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def confirmar_accion(accion: str, req_id: str):
        """
        Teclado de confirmación para acciones.
        
        Args:
            accion: Tipo de acción (aprobar, rechazar, etc.)
            req_id: ID de la requisición
        """
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirmar", callback_data=f"confirm_{accion}_{req_id}"),
                InlineKeyboardButton("❌ Cancelar", callback_data="cancel"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def volver_requisiciones():
        """Teclado simple para volver a requisiciones."""
        keyboard = [
            [
                InlineKeyboardButton("🔙 Volver a Requisiciones", callback_data="mis_req"),
            ],
            [
                InlineKeyboardButton("🏠 Menú Principal", callback_data="menu_principal"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def acciones_imagen_requisicion(req_id: str, estado: str, es_supervisor: bool = False, es_directivo: bool = False):
        """
        Teclado con acciones disponibles después de mostrar la imagen.
        
        Args:
            req_id: ID de la requisición
            estado: Estado actual de la requisición
            es_supervisor: Si el usuario es supervisor
            es_directivo: Si el usuario es directivo
        """
        keyboard = []
        
        # Botón para ver detalles completos
        keyboard.append([
            InlineKeyboardButton("📄 Ver Detalles Completos", callback_data=f"ver_req_{req_id}"),
        ])
        
        # Acciones según estado y permisos
        if estado == "pendiente" and es_supervisor:
            keyboard.append([
                InlineKeyboardButton("✅ Aprobar (Supervisor)", callback_data=f"aprobar_sup_{req_id}"),
                InlineKeyboardButton("❌ Rechazar", callback_data=f"rechazar_{req_id}"),
            ])
        elif estado == "supervisor" and es_directivo:
            keyboard.append([
                InlineKeyboardButton("✅ Aprobar (Directivo)", callback_data=f"aprobar_dir_{req_id}"),
                InlineKeyboardButton("❌ Rechazar", callback_data=f"rechazar_{req_id}"),
            ])
        elif estado == "autorizada":
            keyboard.append([
                InlineKeyboardButton("📦 Marcar como Surtida", callback_data=f"surtir_{req_id}"),
            ])
        elif estado == "surtida":
            keyboard.append([
                InlineKeyboardButton("🔒 Cerrar Requisición", callback_data=f"cerrar_{req_id}"),
            ])
        
        # Botones de navegación
        keyboard.append([
            InlineKeyboardButton("🔙 Volver a Requisiciones", callback_data="mis_req"),
        ])
        keyboard.append([
            InlineKeyboardButton("🏠 Menú Principal", callback_data="menu_principal"),
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def acciones_requisicion(req_id: str, estado: str, es_supervisor: bool = False, es_directivo: bool = False):
        """
        Teclado con acciones disponibles para una requisición.
        
        Args:
            req_id: ID de la requisición
            estado: Estado actual de la requisición
            es_supervisor: Si el usuario es supervisor
            es_directivo: Si el usuario es directivo
        """
        keyboard = []
        
        # Botón para ver detalles
        keyboard.append([
            InlineKeyboardButton("📄 Ver Detalles", callback_data=f"ver_detalles_{req_id}"),
        ])
        
        # Acciones según estado y permisos
        if estado == "pendiente" and es_supervisor:
            keyboard.append([
                InlineKeyboardButton("✅ Aprobar (Supervisor)", callback_data=f"aprobar_sup_{req_id}"),
                InlineKeyboardButton("❌ Rechazar", callback_data=f"rechazar_{req_id}"),
            ])
        
        elif estado == "supervisor" and es_directivo:
            keyboard.append([
                InlineKeyboardButton("✅ Aprobar (Directivo)", callback_data=f"aprobar_dir_{req_id}"),
                InlineKeyboardButton("❌ Rechazar", callback_data=f"rechazar_{req_id}"),
            ])
        
        elif estado == "autorizada":
            keyboard.append([
                InlineKeyboardButton("📦 Marcar como Surtida", callback_data=f"surtir_{req_id}"),
            ])
        
        elif estado == "surtida":
            keyboard.append([
                InlineKeyboardButton("🔒 Cerrar Requisición", callback_data=f"cerrar_{req_id}"),
            ])
        
        # Botón para volver
        keyboard.append([
            InlineKeyboardButton("🔙 Volver", callback_data="menu_principal"),
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @classmethod
    def lista_requisiciones(cls, requisiciones, page: int = 1, items_per_page: int = 10, show_actions: bool = True):
        """
        Teclado con lista paginada de requisiciones optimizada para hasta 200 registros.
        
        Args:
            requisiciones: Lista de requisiciones (puede ser un QuerySet o lista)
            page: Página actual (1-based)
            items_per_page: Número de elementos por página (máx 10 para mejor rendimiento)
            show_actions: Si se muestran botones de acción
            
        Returns:
            InlineKeyboardMarkup: Teclado con la lista paginada
        """
        # Asegurar que items_per_page no sea muy grande
        items_per_page = min(max(1, items_per_page), 10)
        
        # Convertir a lista si es necesario
        if not isinstance(requisiciones, list):
            requisiciones = list(requisiciones)
        
        # Calcular total de páginas
        total_requisiciones = len(requisiciones)
        total_pages = max(1, (total_requisiciones + items_per_page - 1) // items_per_page)
        page = max(1, min(page, total_pages))  # Asegurar que esté en rango
        
        # Obtener solo los registros necesarios para la página actual
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        requisiciones_pagina = requisiciones[start_idx:end_idx]
        
        keyboard = []
        
        # Agregar botones de requisiciones
        for req in requisiciones_pagina:
            estado_emoji = {
                'pendiente': '🟡',
                'supervisor': '🟠',
                'autorizada': '🟢',
                'surtida': '🔵',
                'cerrada': '⚫',
                'rechazada': '🔴',
            }
            
            # Obtener atributos de forma segura
            estado = getattr(req, 'estado', '').lower()
            emoji = estado_emoji.get(estado, '⚪')
            req_id = getattr(req, 'id', 'SIN-ID')
            obra = getattr(req, 'obra', 'Sin obra')
            obra = (obra[:15] + '...') if len(obra) > 15 else obra
            
            # Texto del botón con información resumida
            button_text = f"{emoji} {req_id} | {obra} | {estado[:10]}"
            
            # Botón principal para ver detalles
            row = [
                InlineKeyboardButton(
                    button_text,
                    callback_data=f"ver_img_{req_id}"
                )
            ]
            
            # Agregar botones de acción si es necesario
            if show_actions and estado == 'pendiente':
                row.extend([
                    InlineKeyboardButton("✅", callback_data=f"aprovar_{req_id}"),
                    InlineKeyboardButton("❌", callback_data=f"rechazar_{req_id}")
                ])
            
            keyboard.append(row)
        
        # Botones de navegación
        if total_pages > 1:
            nav_buttons = []
            
            # Botón Primera página
            if page > 2:
                nav_buttons.append(
                    InlineKeyboardButton("⏪ 1", callback_data="page_1")
                )
            
            # Botón Anterior
            if page > 1:
                nav_buttons.append(
                    InlineKeyboardButton("⬅️", callback_data=f"page_{page-1}")
                )
            
            # Indicador de página actual (botón inactivo)
            nav_buttons.append(
                InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop")
            )
            
            # Botón Siguiente
            if page < total_pages:
                nav_buttons.append(
                    InlineKeyboardButton("➡️", callback_data=f"page_{page+1}")
                )
            
            # Botón Última página
            if page < total_pages - 1:
                nav_buttons.append(
                    InlineKeyboardButton(f"{total_pages} ⏩", callback_data=f"page_{total_pages}")
                )
            
            if nav_buttons:
                keyboard.append(nav_buttons)
        
        # Botón para volver al menú
        keyboard.append([
            InlineKeyboardButton("🔙 Volver al menú", callback_data="menu_principal")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def seleccionar_bloque(bloques):
        """
        Teclado para seleccionar un bloque.
        
        Args:
            bloques: Lista de bloques disponibles
        """
        keyboard = []
        
        for bloque in bloques:
            keyboard.append([
                InlineKeyboardButton(
                    bloque.nombre,
                    callback_data=f"bloque_{bloque.id}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("❌ Cancelar", callback_data="cancel"),
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def seleccionar_empleado(empleados):
        """
        Teclado para seleccionar un empleado.
        
        Args:
            empleados: Lista de empleados disponibles
        """
        keyboard = []
        
        for empleado in empleados[:10]:  # Limitar a 10 para no saturar
            keyboard.append([
                InlineKeyboardButton(
                    empleado.nombre,
                    callback_data=f"empleado_{empleado.id}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("❌ Cancelar", callback_data="cancel"),
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def agregar_articulos():
        """Teclado para agregar artículos a una requisición."""
        keyboard = [
            [
                InlineKeyboardButton("➕ Agregar Artículo", callback_data="add_articulo"),
            ],
            [
                InlineKeyboardButton("✅ Finalizar Requisición", callback_data="finalizar_req"),
                InlineKeyboardButton("❌ Cancelar", callback_data="cancel_req"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def estados_filtro():
        """Teclado para filtrar requisiciones por estado."""
        keyboard = [
            [
                InlineKeyboardButton("🟡 Pendientes", callback_data="filtro_pendiente"),
                InlineKeyboardButton("🟠 Supervisor", callback_data="filtro_supervisor"),
            ],
            [
                InlineKeyboardButton("🟢 Autorizadas", callback_data="filtro_autorizada"),
                InlineKeyboardButton("🔵 Surtidas", callback_data="filtro_surtida"),
            ],
            [
                InlineKeyboardButton("⚫ Cerradas", callback_data="filtro_cerrada"),
                InlineKeyboardButton("🔴 Rechazadas", callback_data="filtro_rechazada"),
            ],
            [
                InlineKeyboardButton("📋 Todas", callback_data="filtro_todas"),
            ],
            [
                InlineKeyboardButton("🔙 Volver", callback_data="menu_principal"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def seleccionar_supervisor(supervisores):
        """
        Teclado para seleccionar un supervisor (dinámico desde BD).

        Args:
            supervisores: Lista de empleados con rol supervisor

        Returns:
            InlineKeyboardMarkup: Teclado con supervisores de la BD
        """
        keyboard = []
        
        # Agregar botones para cada supervisor
        for supervisor in supervisores:
            keyboard.append([
                InlineKeyboardButton(
                    f"👤 {supervisor.nombre}",
                    callback_data=f"supervisor_{supervisor.id}"
                )
            ])
        
        # Si no hay supervisores, mostrar mensaje
        if not supervisores:
            keyboard.append([
                InlineKeyboardButton("⚠️ Sin supervisores disponibles", callback_data="none"),
            ])
        
        # Botón de cancelar
        keyboard.append([
            InlineKeyboardButton("❌ Cancelar", callback_data="cancel"),
        ])
        
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def seleccionar_especialidad():
        """
        Teclado para seleccionar una especialidad.

        Returns:
            InlineKeyboardMarkup: Teclado con especialidades
        """
        keyboard = [
            [
                InlineKeyboardButton("🔧 Plomería", callback_data="especialidad_Plomería"),
                InlineKeyboardButton("⚡ Electricidad", callback_data="especialidad_Electricidad"),
            ],
            [
                InlineKeyboardButton("🏗️ Obra Civil", callback_data="especialidad_Obra Civil"),
                InlineKeyboardButton("🪟 Vidrio y Canceleria", callback_data="especialidad_Vidrio y Canceleria"),
            ],
            [
                InlineKeyboardButton("🎨 Pintura y Tablaroca", callback_data="especialidad_Pintura y Tablaroca"),
                InlineKeyboardButton("🔨 Herrería", callback_data="especialidad_Herrería"),
            ],
            [
                InlineKeyboardButton("🔧 Herramienta", callback_data="especialidad_Herramienta"),
                InlineKeyboardButton(" limpieza", callback_data="especialidad_Limpieza"),
            ],
            [
                InlineKeyboardButton("❌ Cancelar", callback_data="cancel"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def ubicacion_no_aplica():
        """Teclado con opción No Aplica para ubicación."""
        keyboard = [
            [InlineKeyboardButton("🚫 No Aplica", callback_data="ubicacion_na")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def fecha_rapida():
        """Teclado con opciones rápidas de fecha."""
        from datetime import date, timedelta
        hoy = date.today()
        manana = hoy + timedelta(days=1)
        dos_semanas = hoy + timedelta(days=14)
        
        keyboard = [
            [InlineKeyboardButton(f"📅 Hoy ({hoy.strftime('%d/%m/%Y')})", callback_data=f"fecha_{hoy.strftime('%d/%m/%Y')}")],
            [InlineKeyboardButton(f"📅 Mañana ({manana.strftime('%d/%m/%Y')})", callback_data=f"fecha_{manana.strftime('%d/%m/%Y')}")],
            [InlineKeyboardButton(f"📅 En 2 semanas ({dos_semanas.strftime('%d/%m/%Y')})", callback_data=f"fecha_{dos_semanas.strftime('%d/%m/%Y')}")],
            [InlineKeyboardButton("✏️ Ingresar otra fecha", callback_data="fecha_manual")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def cancelar():
        """Teclado simple con botón de cancelar."""
        keyboard = [
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def esperando_imagen():
        """Teclado mientras espera la imagen."""
        keyboard = [
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def ayuda():
        """Teclado para la sección de ayuda con botón de regresar."""
        keyboard = [
            [InlineKeyboardButton("🔙 Regresar al Menú", callback_data="menu_principal")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def main_menu():
        """Teclado del menú principal (alias de menu_principal)."""
        return Keyboards.menu_principal()
