Este documento define el estándar de calidad. Los agentes revisores evalúan código contra este archivo. Si no está aquí, no es un requisito.

## Arquitectura

the cliente servidor, entre un front y un back, Cada uno de estos tiene:

- back: hexagonal
- front: Modularizada

## Rules

back:

- Inmudeability by defauld. @dataclass(frozen=True). modify = create a new instance.
- Toda escritura a notes.json se hace primero en un archivo temporal y luego os.replace(). Nunca dejar el archivo a medio escribir.
- Errores explícitos. Las funciones que pueden fallar (id no existe, archivo corrupto) lanzan excepciones nombradas, no devuelven None

Front

- Toda escritura a notes.json se hace primero en un archivo temporal y luego os.replace(). Nunca dejar el archivo a medio escribir.

## no not

Not read/write the file in a bucle. Load in the beginin, modify at memory, save at the end.
