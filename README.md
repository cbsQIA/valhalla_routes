# Ejemplo sencillo de optimización de rutas


Usa la api de `valhalla` en local y llama:
- [/isochrone](https://valhalla.github.io/valhalla/api/isochrone/api-reference/):  Comprueba que los puntos son alcanzables a cierta distancia

 - [/optimized_routes](https://valhalla.github.io/valhalla/api/optimized/api-reference/):  Optimiza la ruta entre puntos, en caso de fallar (por distancia) usa /routes`
    

Se debe descargar el [tile](https://valhalla.github.io/valhalla/mjolnir/why_tiles/) necesario para las busquedas. Se parte el mapa del mundo en una cuadricula, cada cuadrado es un `tile`. De esta forma no tienes que tener todos los `tiles` del planeta, solo los que te interesa.

Ejemplo de docker para levantar `Valhalla`:

```yml
  valhalla:
    image: ghcr.io/nilsnolde/docker-valhalla/valhalla:latest
    container_name: valhalla
    volumes:
      - ./valhalla_files:/custom_files
    environment:
      - tile_urls=https://download.geofabrik.de/europe/spain/andalucia-latest.osm.pbf
      - serve_tiles=True
      - use_tiles_ignore_pbf=False
      - force_rebuild=False
      - build_tiles=True              
      - build_tar=True
      - server_threads=1
    restart: unless-stopped
```
Se usa tile_urls en download para descargar el tile de andalucia. Buscar en [Geofabrik](https://download.geofabrik.de/) el que os interese y ponerlo en el environment

> Las funciones están hechas de forma asíncrona para implementarse en una API.
> Por eso se usa httpx, async,... y en streamlit asyncio para correrlas.