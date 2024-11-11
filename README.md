# Segder
Sistema de versionado para el proyecto de Segder

## Parte 1
<img width="440" alt="image" src="https://github.com/user-attachments/assets/f28b7f43-7633-44b2-a98a-d7ded6feb787">

1. En una primera fase, la aplicación se comunica (mediante un conjunto de comandos a definir por el estudiante) con el servidor de contenidos, para conocer qué imágenes y vídeos tiene disponibles éste último. Tenga en cuenta que estos contenidos podrán estar encriptados con un cifrador simétrico. Así pues, una vez decidido qué contenido se desea descargar, la aplicación se lo solicita al servidor de contenidos y éste se lo envía.

2. En una segunda fase, la aplicación debe comprobar si el contenido digital está protegido mediante cifrado o no lo está. Si no está cifrado, no debe hacer nada adicional, simplemente indicárselo al usuario y ponerle el fichero a su disposición. En el caso de que esté cifrado, la aplicación debe tratar de conseguir la contraseña de descifrado que debe solicitar al servidor
 
## Parte 2

Como extensión a la funcionalidad ya definida, el sistema desarrollado debe contemplar los siguientes
aspectos adicionales:
<li>
  <ol>
    1. Tal y como se ha dicho, los contenidos digitales pueden ser de dos tipos: imágenes y vídeos.
Cuando se trate de imágenes, el servidor de contenidos incluirá en la imagen enviada una
marca de agua visible cuyo contenido dependerá del usuario al que le esté enviando la
información y que sirva para identificarlo.
  </ol>
<ol>
  El mensaje de solicitud de la clave de cifrado deberá estar firmado digitalmente por la
aplicación.
</ol>
</li>

## Parte 3

<img width="440" alt="image" src="https://github.com/user-attachments/assets/76c218fd-1213-4261-929c-806d3765ab5c">

1. Idéntico a lo descrito para el paso 1 de la figura anterior.

2. La UA, cuando comprueba que la imagen o vídeo está cifrado, pide al CDM un mensaje de
solicitud de licencia. El CDM prepara ese mensaje, lo firma digitalmente y se lo envía a la UA.
Tenga en cuenta que la comunicación entre la UA y el CDM debe estar también cifrada (con
cifrado simétrico cuya clave se debe haber establecido previamente con cifrado asimétrico).

3. La UA reenvía el mensaje de solicitud de licencia al servidor de licencias y recibe la respuesta de éste. Considere lo indicado anteriormente en cuanto a que dicha comunicación debe estar cifrada (con cifrado simétrico cuya clave se debe haber establecido previamente con cifrado asimétrico) y que la solicitud debe estar firmada digitalmente.

4. La UA reenvía la licencia (que incluye la clave de descifrado simétrico) al CDM, el cual
desencripta la imagen o vídeo.

Como observará en dicha figura, el CDM es la entidad encargada de preparar y enviar la solicitud de licencia a la aplicación, que la reenvía al servidor de licencias. Por otro lado, la respuesta del servidor de licencia debe llegar cifrada al CDM, pero lo hace a través de la UA. Finalmente, es el CDM quien interpreta la respuesta del servidor y desencripta el contenido digital, poniéndolo a disposición del usuario.

Algunas consideraciones adicionales que aplican a todo el trabajo son:

* Cuando emplee cifrado simétrico, emplee el cifrador AES con una contraseña de 128 bits. En
cuanto al modo de funcionamiento, emplee el modo CTR o CBC.
* Cuando emplee cifrado asimétrico (incluyendo la firma digital), emplee el algoritmo RSA. De manera más concreta, emplee la generación y el manejo de claves que proporciona la biblioteca cryptography (por ejemplo, con los métodos generate_private_key() y public_key()), pero realice el cifrado y el descifrado con la función pow proporcionada por
Python.


## A Entregar
* **Vídeo explicativo** y demostrativo del trabajo desarrollado. Cada grupo de trabajo debe grabar un vídeo donde se muestre el funcionamiento del trabajo realizado, debiéndose mostrar e indicar claramente las funcionalidades implementadas con éxito y a qué calificación, a juicio del grupo, puede optar el trabajo entregado en función de las funcionalidades implementadas. La duración máxima de cada vídeo es de 5 minutos.
* **Memoria del proyecto.** En dicha memoria debe indicarse el trabajo realizado así como incluir el código fuente de los programas desarrollados y capturas de pantalla donde se vea el funcionamiento. Además, como parte de esa memoria, deben desglosarse las tareas que ha realizado cada uno de los integrantes del grupo de trabajo.
* **Presentación oral pública** del funcionamiento del trabajo desarrollado. _(pedir antes del 8 de enero)_

## Evaluación

*  Si se completa con éxito solo la parte I, la calificación máxima que puede alcanzarse es de
0,75 puntos.
* Si se completan con éxito las partes I y II, la calificación máxima que puede alcanzarse es de
1,25 puntos.
* Si se completan con éxito las partes I, II y III, la calificación máxima que puede alcanzarse es
de 1,5 puntos.
* En el caso de que haya realizado las partes I, II y III, puede optar a la máxima calificación (2
puntos) presentando de manera oral el trabajo.

