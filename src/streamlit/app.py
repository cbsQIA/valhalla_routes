import streamlit as st
import folium
from streamlit_folium import st_folium
import asyncio
import polyline
from valhalla.entities import Coordinate
from valhalla.valhalla import get_optimal_route, filter_by_location_polygon

# Configuración de la página
st.set_page_config(
    page_title="Valhalla Route Tester",
    page_icon="🗺️",
    layout="wide"
)

st.title("🗺️ Valhalla Route Tester")
st.markdown("Prueba las funcionalidades de rutas y polígonos de isócrona")

# Inicializar estado de la sesión
if 'locations' not in st.session_state:
    st.session_state.locations = []
if 'polygon_center' not in st.session_state:
    st.session_state.polygon_center = None
if 'route_result' not in st.session_state:
    st.session_state.route_result = None
if 'filtered_coords' not in st.session_state:
    st.session_state.filtered_coords = []
if 'current_mode' not in st.session_state:
    st.session_state.current_mode = "Ruta Óptima"
if 'has_filtered' not in st.session_state:
    st.session_state.has_filtered = False
if 'route_costing_label' not in st.session_state:
    st.session_state.route_costing_label = "🚗 Auto"
if 'polygon_costing_label' not in st.session_state:
    st.session_state.polygon_costing_label = "🚗 Auto"

# Opciones de tipo de transporte (común para todo)
costing_options = {
    "🚗 Auto": "auto",
    "🚶 Peatón": "pedestrian",
    "🚴 Bicicleta": "bicycle"
}

# Sidebar para controles
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Configuración de Valhalla (si lo usas vía Settings, esto es solo visual)
    st.subheader("Valhalla API")
    valhalla_url = st.text_input(
        "URL de Valhalla",
        value="http://localhost:8002",
        help="URL del servidor Valhalla"
    )
    
    st.divider()
    
    # Selector de funcionalidad
    st.subheader("Funcionalidad")
    mode = st.radio(
        "Selecciona el modo:",
        ["Ruta Óptima", "Filtro por Polígono"],
        help="Elige qué funcionalidad quieres probar"
    )
    
    # Detectar cambio de modo y reiniciar
    if mode != st.session_state.current_mode:
        st.session_state.current_mode = mode
        st.session_state.locations = []
        st.session_state.polygon_center = None
        st.session_state.route_result = None
        st.session_state.filtered_coords = []
        st.session_state.has_filtered = False
        st.rerun()
    
    st.divider()
    
    if mode == "Ruta Óptima":
        st.subheader("📍 Agregar Ubicaciones")
        st.markdown("Haz clic en el mapa para agregar puntos de ruta")
        
        # Selector de tipo de transporte para la ruta
        route_costing_label = st.selectbox(
            "Tipo de transporte",
            options=list(costing_options.keys()),
            index=list(costing_options.keys()).index(st.session_state.route_costing_label),
            key="route_costing_select",
            help="Selecciona el modo de transporte para calcular la ruta óptima"
        )
        route_costing = costing_options[route_costing_label]
        st.session_state.route_costing_label = route_costing_label
        
        # Mostrar ubicaciones actuales
        if st.session_state.locations:
            st.write(f"**Ubicaciones ({len(st.session_state.locations)}):**")
            for i, loc in enumerate(st.session_state.locations):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(f"{i+1}. ({loc['lat']:.5f}, {loc['lng']:.5f})")
                with col2:
                    if st.button("🗑️", key=f"del_{i}"):
                        st.session_state.locations.pop(i)
                        st.session_state.route_result = None
                        st.rerun()
        
        if st.button("🗑️ Limpiar todo", use_container_width=True):
            st.session_state.locations = []
            st.session_state.route_result = None
            st.rerun()
        
        if st.button(
            "🚗 Calcular Ruta",
            disabled=len(st.session_state.locations) < 2,
            use_container_width=True,
            type="primary"
        ):
            with st.spinner("Calculando ruta óptima..."):
                try:
                    coords = [
                        Coordinate(lat=loc['lat'], lng=loc['lng'])
                        for loc in st.session_state.locations
                    ]
                    result = asyncio.run(get_optimal_route(coords, costing=route_costing))
                    st.session_state.route_result = result
                    if result:
                        st.success("✅ Ruta calculada exitosamente")
                    else:
                        st.error("❌ No se pudo calcular la ruta")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al calcular ruta: {e}")
    
    else:  # Filtro por Polígono
        st.subheader("⏱️ Configuración de Isócrona")
        
        # Selector de tipo de transporte para isócrona
        polygon_costing_label = st.selectbox(
            "Tipo de transporte",
            options=list(costing_options.keys()),
            index=list(costing_options.keys()).index(st.session_state.polygon_costing_label),
            key="polygon_costing_select",
            help="Selecciona el modo de transporte para calcular la isócrona"
        )
        costing = costing_options[polygon_costing_label]
        st.session_state.polygon_costing_label = polygon_costing_label
        
        minutes = st.slider(
            "Tiempo (minutos)",
            min_value=5,
            max_value=60,
            value=15,
            step=5
        )
        
        st.markdown("**1.** Haz clic en el mapa para establecer el centro")
        st.markdown("**2.** Haz clic para agregar puntos a verificar")
        
        if st.session_state.polygon_center:
            st.success(
                f"Centro: ({st.session_state.polygon_center['lat']:.5f}, "
                f"{st.session_state.polygon_center['lng']:.5f})"
            )
            
            if st.button("🔄 Cambiar centro"):
                st.session_state.polygon_center = None
                st.session_state.filtered_coords = []
                st.session_state.has_filtered = False
                st.rerun()
        
        if st.button(
            "🔍 Filtrar por Polígono",
            disabled=not st.session_state.polygon_center or not st.session_state.locations,
            use_container_width=True,
            type="primary"
        ):
            with st.spinner(f"Filtrando coordenadas ({polygon_costing_label})..."):
                try:
                    center = Coordinate(**st.session_state.polygon_center)
                    coords = [
                        Coordinate(lat=loc['lat'], lng=loc['lng'])
                        for loc in st.session_state.locations
                    ]
                    filtered = asyncio.run(
                        filter_by_location_polygon(center, minutes, coords, costing)
                    )
                    st.session_state.filtered_coords = filtered
                    st.session_state.has_filtered = True
                    st.success(f"✅ {len(filtered)}/{len(coords)} puntos alcanzables")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al filtrar: {e}")
        
        if st.button("🗑️ Reiniciar", use_container_width=True):
            st.session_state.polygon_center = None
            st.session_state.locations = []
            st.session_state.filtered_coords = []
            st.session_state.has_filtered = False
            st.rerun()

# Área principal - Mapa
col1, col2 = st.columns([2, 1])

with col1:
    # Crear mapa centrado en Málaga
    m = folium.Map(
        location=[36.7213, -4.4214],  # Málaga
        zoom_start=12,
        tiles="OpenStreetMap"
    )
    
    # Agregar marcadores según el modo
    if mode == "Ruta Óptima":
        # Agregar marcadores numerados para la ruta
        for i, loc in enumerate(st.session_state.locations):
            folium.Marker(
                location=[loc['lat'], loc['lng']],
                popup=f"Punto {i+1}",
                icon=folium.Icon(color='blue', icon='info-sign', prefix='glyphicon'),
                tooltip=f"Ubicación {i+1}"
            ).add_to(m)
        
        # Si hay resultado de ruta, dibujar las piernas (legs)
        if st.session_state.route_result:
            trip = st.session_state.route_result
            colors = [
                'blue', 'red', 'green', 'purple', 'orange', 'darkred', 'lightred',
                'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'pink'
            ]
            
            for leg_idx, leg in enumerate(trip.legs):
                if leg.shape:
                    try:
                        # Valhalla usa Polyline6
                        coords = polyline.decode(leg.shape, precision=6, geojson=False)
                        folium.PolyLine(
                            locations=coords,
                            color=colors[leg_idx % len(colors)],
                            weight=4,
                            opacity=0.8,
                            popup=(
                                f"Pierna {leg_idx + 1}<br>"
                                f"Distancia: {leg.summary.length:.2f} km<br>"
                                f"Tiempo: {leg.summary.time/60:.1f} min"
                            ),
                            tooltip=f"Pierna {leg_idx + 1}",
                        ).add_to(m)
                    except Exception as e:
                        st.warning(f"Error decodificando shape de pierna {leg_idx + 1}: {e}")
    
    else:  # Filtro por Polígono
        # Marcador del centro
        if st.session_state.polygon_center:
            folium.Marker(
                location=[
                    st.session_state.polygon_center['lat'],
                    st.session_state.polygon_center['lng']
                ],
                popup="Centro de isócrona",
                icon=folium.Icon(color='red', icon='star'),
                tooltip="Centro"
            ).add_to(m)
        
        # Puntos a verificar
        for loc in st.session_state.locations:
            if st.session_state.has_filtered:
                # Ya hemos filtrado → verde/rojo según alcanzable
                is_filtered = any(
                    abs(fc.lat - loc['lat']) < 0.000001 and
                    abs(fc.lng - loc['lng']) < 0.000001
                    for fc in st.session_state.filtered_coords
                )
                color = 'green' if is_filtered else 'red'
                popup = "✅ Dentro del alcance" if is_filtered else "❌ Fuera del alcance"
                tooltip = "Alcanzable" if is_filtered else "No alcanzable"
            else:
                # Todavía NO se ha filtrado → estado neutro
                color = 'blue'
                popup = "⏱️ Pendiente de cálculo"
                tooltip = "Punto a verificar"

            folium.CircleMarker(
                location=[loc['lat'], loc['lng']],
                radius=8,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                weight=2,
                popup=popup,
                tooltip=tooltip,
            ).add_to(m)
    
    # Mostrar el mapa y capturar clics
    map_data = st_folium(
        m,
        width=700,
        height=500,
        key="map"
    )
    
    # Procesar clics en el mapa
    if map_data and map_data.get('last_clicked'):
        lat = map_data['last_clicked']['lat']
        lng = map_data['last_clicked']['lng']
        
        if mode == "Ruta Óptima":
            new_loc = {'lat': lat, 'lng': lng}
            if new_loc not in st.session_state.locations:
                st.session_state.locations.append(new_loc)
                st.session_state.route_result = None  # Reset route when adding new point
                st.rerun()
        else:
            # Si no hay centro, establecerlo
            if not st.session_state.polygon_center:
                st.session_state.polygon_center = {'lat': lat, 'lng': lng}
                st.rerun()
            else:
                # Si ya hay centro, agregar como punto a verificar
                new_loc = {'lat': lat, 'lng': lng}
                if new_loc not in st.session_state.locations:
                    st.session_state.locations.append(new_loc)
                    st.session_state.filtered_coords = []  # Reset filter
                    st.session_state.has_filtered = False
                    st.rerun()

with col2:
    st.subheader("📊 Información")
    
    if mode == "Ruta Óptima":
        st.metric("Ubicaciones", len(st.session_state.locations))
        st.metric("Tipo de transporte", st.session_state.route_costing_label)
        
        if st.session_state.route_result:
            trip = st.session_state.route_result
            st.success("✅ Ruta calculada")
            
            # Mostrar resumen de la ruta
            st.metric("Distancia total", f"{trip.summary.length:.2f} km")
            st.metric("Tiempo total", f"{trip.summary.time/60:.1f} min")
            
            # Detalles adicionales
            with st.expander("📋 Detalles de la ruta"):
                st.write(f"**¿Tiene peajes?** {'Sí' if trip.summary.has_toll else 'No'}")
                st.write(f"**¿Usa autopista?** {'Sí' if trip.summary.has_highway else 'No'}")
                st.write(f"**¿Usa ferry?** {'Sí' if trip.summary.has_ferry else 'No'}")
                
                for i, leg in enumerate(trip.legs):
                    st.write(f"**Pierna {i+1}:**")
                    st.write(f"- Distancia: {leg.summary.length:.2f} km")
                    st.write(f"- Tiempo: {leg.summary.time/60:.1f} min")
                    st.write(f"- Maniobras: {len(leg.maneuvers)}")
        elif len(st.session_state.locations) >= 2:
            st.info("👆 Haz clic en 'Calcular Ruta'")
        else:
            st.warning("⚠️ Agrega al menos 2 ubicaciones")
    
    else:
        st.metric("Tipo de transporte", st.session_state.polygon_costing_label)
        st.metric("Tiempo", f"{minutes} min")
        st.metric("Puntos totales", len(st.session_state.locations))
        
        if st.session_state.filtered_coords:
            alcanzables = len(st.session_state.filtered_coords)
            total = len(st.session_state.locations)
            st.metric("Puntos alcanzables", f"{alcanzables}/{total}")
            
            porcentaje = (alcanzables / total * 100) if total > 0 else 0
            st.progress(porcentaje / 100)
            st.caption(f"{porcentaje:.1f}% alcanzable")
        else:
            st.metric("Puntos alcanzables", "—")
        
        if st.session_state.polygon_center:
            st.success("✅ Centro establecido")
            if st.session_state.locations:
                st.info("👆 Agrega más puntos o calcula")
            else:
                st.info("👆 Agrega puntos haciendo clic en el mapa")
        else:
            st.info("👆 Haz clic en el mapa para establecer el centro")

# Footer
st.divider()
st.markdown("""
### 📝 Instrucciones
1. **Ruta Óptima**: Haz clic en el mapa para agregar puntos de ruta, luego calcula la ruta óptima. Las piernas se dibujan con diferentes colores.
2. **Filtro por Polígono**: Establece un centro primero, luego agrega puntos. Los puntos verdes están dentro del tiempo especificado, los rojos fuera.

💡 **Tip**: Al cambiar de modo, los puntos se reinician automáticamente.
""")
