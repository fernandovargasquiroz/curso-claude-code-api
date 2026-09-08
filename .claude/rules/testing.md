# Testing

Antes de corregir cualquier fallo reportado, se reproduce primero con un
caso real contra el sistema: un test que se ejecuta en rojo, o una
ejecución real (contra la API corriendo, una migración, un comando) que
deja evidencia del fallo. La corrección se escribe después, nunca antes.

La corrección nunca oculta esa reproducción: el test o la evidencia que la
disparó se queda tal como se escribió — no se debilita, no se borra, ni se
ajusta para que deje de fallar sin que el comportamiento corregido lo
explique.
