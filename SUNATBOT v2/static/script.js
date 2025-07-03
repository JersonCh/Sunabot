function processMarkdown(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
    .replace(/^(\d+\.\s)/gm, '<strong>$1</strong>')
    .replace(/^-\s/gm, '• ')
    .replace(/(\d+\.\s\*\*)(.*?)(\*\*)/g, '<strong>$1$2</strong>')
    .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" style="color: #800000;">$1</a>');
}

let currentSpeech = null;
let currentSpeechText = '';
let currentSpeechButton = null;
let isIntentionalStop = false; 
let availableVoices = [];

function loadVoices() {
  return new Promise((resolve) => {
    const voices = speechSynthesis.getVoices();
    if (voices.length > 0) {
      availableVoices = voices;
      resolve(voices);
    } else {
      speechSynthesis.onvoiceschanged = () => {
        availableVoices = speechSynthesis.getVoices();
        resolve(availableVoices);
      };
    }
  });
}

function getBestSpanishVoice() {
  const spanishVoices = availableVoices.filter(voice => 
    voice.lang.startsWith('es-') || voice.lang === 'es'
  );
  
  if (spanishVoices.length === 0) {
    return null; 
  }
  
  const priorities = ['es-ES', 'es-MX', 'es-US', 'es-AR', 'es-CO'];
  
  for (const priority of priorities) {
    const voice = spanishVoices.find(v => v.lang === priority);
    if (voice) return voice;
  }
  
  return spanishVoices[0];
}

document.addEventListener('DOMContentLoaded', function() {
  if ('speechSynthesis' in window) {
    loadVoices();
  }
});

function speakText(button) {
  if (!('speechSynthesis' in window)) {
    alert('Tu navegador no soporta la función de lectura en voz alta.');
    return;
  }

  const messageContent = button.closest('.message-content');
  
  if (currentSpeechButton === button && currentSpeech) {
    if (speechSynthesis.speaking && !speechSynthesis.paused) {
      speechSynthesis.pause();
      updateSpeechButtons(button, 'paused');
      return;
    } else if (speechSynthesis.paused) {
      speechSynthesis.resume();
      updateSpeechButtons(button, 'playing');
      return;
    }
  }
  
  stopCurrentSpeech();
  
  const cleanText = getCleanTextFromMessage(messageContent);
  
  if (!cleanText) {
    alert('No hay texto para leer.');
    return;
  }
  
  currentSpeechText = cleanText;
  currentSpeechButton = button;
  
  startSpeech(cleanText, button);
}

function restartSpeech(button) {
  if (currentSpeechButton === button && currentSpeechText) {
    isIntentionalStop = true; 
    stopCurrentSpeech();
    setTimeout(() => {
      currentSpeechButton = button;
      startSpeech(currentSpeechText, button);
    }, 300);
  }
}

function stopSpeech(button) {
  if (currentSpeechButton === button) {
    stopCurrentSpeech();
  }
}

function stopCurrentSpeech() {
  if (currentSpeech) {
    isIntentionalStop = true;
    
    try {
      speechSynthesis.cancel();
    } catch (e) {
      console.log('Error al cancelar síntesis:', e);
    }
    
    if (currentSpeechButton) {
      updateSpeechButtons(currentSpeechButton, 'stopped');
    }
    
    currentSpeech = null;
    currentSpeechButton = null;
    currentSpeechText = '';
    
    setTimeout(() => {
      isIntentionalStop = false;
    }, 500);
  }
}

function startSpeech(text, button) {
  currentSpeech = new SpeechSynthesisUtterance(text);
  
  const bestVoice = getBestSpanishVoice();
  if (bestVoice) {
    currentSpeech.voice = bestVoice;
    currentSpeech.lang = bestVoice.lang;
  } else {
    currentSpeech.lang = 'es-ES'; 
  }
  
  currentSpeech.rate = 0.85; 
  currentSpeech.pitch = 1;
  currentSpeech.volume = 0.9; 

  currentSpeech.onstart = function() {
    console.log('Iniciando lectura de respuesta');
    updateSpeechButtons(button, 'playing');
  };

  currentSpeech.onpause = function() {
    console.log('Lectura pausada');
    updateSpeechButtons(button, 'paused');
  };

  currentSpeech.onresume = function() {
    console.log('Lectura reanudada');
    updateSpeechButtons(button, 'playing');
  };

  currentSpeech.onend = function() {
    console.log('Lectura terminada');
    
    if (!isIntentionalStop) {
      updateSpeechButtons(button, 'stopped');
    }
    
    currentSpeech = null;
    currentSpeechButton = null;
    currentSpeechText = '';
    isIntentionalStop = false; 
  };

  currentSpeech.onerror = function(event) {
    console.error('Error en síntesis de voz:', event.error);
    
    if (!isIntentionalStop) {
      if (event.error !== 'canceled' && event.error !== 'interrupted') {
        alert('Error al reproducir el audio. Inténtalo de nuevo.');
      }
    }
    
    updateSpeechButtons(button, 'stopped');
    currentSpeech = null;
    currentSpeechButton = null;
    currentSpeechText = '';
    isIntentionalStop = false; 
  };

  speechSynthesis.speak(currentSpeech);
}

function updateSpeechButtons(button, state) {
  const messageActions = button.closest('.message-actions');
  
  const existingControls = messageActions.querySelectorAll('.speech-control');
  existingControls.forEach(btn => btn.remove());
  
  switch(state) {
    case 'playing':
      button.innerHTML = '⏸️';
      button.title = 'Pausar lectura';
      button.classList.add('speaking');
      
      const stopBtn = document.createElement('button');
      stopBtn.className = 'speak-btn speech-control stop-btn';
      stopBtn.innerHTML = '⏹️';
      stopBtn.title = 'Detener lectura';
      stopBtn.onclick = () => stopSpeech(button);
      messageActions.appendChild(stopBtn);
      break;
      
    case 'paused':
      button.innerHTML = '▶️';
      button.title = 'Continuar lectura';
      button.classList.add('speaking');
      
      const restartBtn = document.createElement('button');
      restartBtn.className = 'speak-btn speech-control restart-btn';
      restartBtn.innerHTML = '🔄';
      restartBtn.title = 'Reiniciar lectura';
      restartBtn.onclick = () => restartSpeech(button);
      messageActions.appendChild(restartBtn);
      
      const stopBtn2 = document.createElement('button');
      stopBtn2.className = 'speak-btn speech-control stop-btn';
      stopBtn2.innerHTML = '⏹️';
      stopBtn2.title = 'Detener lectura';
      stopBtn2.onclick = () => stopSpeech(button);
      messageActions.appendChild(stopBtn2);
      break;
      
    case 'stopped':
    default:
      button.innerHTML = '🔊';
      button.title = 'Escuchar respuesta';
      button.classList.remove('speaking');
      break;
  }
}

function getCleanTextFromMessage(messageContent) {
  let textToSpeak = messageContent.cloneNode(true);
  const actions = textToSpeak.querySelector('.message-actions');
  if (actions) actions.remove();
  
  let cleanText = textToSpeak.textContent || textToSpeak.innerText || '';
  
  cleanText = cleanText
    .replace(/•/g, 'punto') 
    .replace(/\s+/g, ' ')
    .replace(/([.!?])\s*([A-Z])/g, '$1 $2') 
    .replace(/S\/\./g, 'sin número')
    .replace(/RUC/g, 'ruc') 
    .replace(/SUNAT/g, 'Sunat') 
    .replace(/IGV/g, 'i-ge-uve')
    .replace(/UIT/g, 'u-i-te') 
    .replace(/DJ/g, 'declaración jurada') 
    .replace(/Nº/g, 'número') 
    .replace(/%/g, 'por ciento') 
    .replace(/(\d+)%/g, '$1 por ciento')
    .replace(/Art\./g, 'artículo') 
    .replace(/Inc\./g, 'inciso') 
    .replace(/www\./g, 'doble uve doble uve doble uve punto')
    .trim();
    
  return cleanText;
}

// Función principal para enviar mensajes directamente a Gemini
function sendMessage() {
  const input = document.getElementById("userInput");
  const mensaje = input.value.trim();
  
  if (!mensaje) {
    alert("Por favor, escribe tu consulta.");
    return;
  }
  
  // Guardar mensaje para retry
  window.lastMessage = mensaje;
  
  const chatContent = document.getElementById("chat-content");
  
  // Mostrar mensaje del usuario
  const userDiv = document.createElement("div");
  userDiv.className = "message user";
  userDiv.innerHTML = `
    <div class="message-avatar">👤</div>
    <div class="message-content">${mensaje}</div>
  `;
  chatContent.appendChild(userDiv);
  
  // Limpiar input
  input.value = "";
  
  // Mostrar indicador de carga
  const loadingDiv = document.createElement("div");
  loadingDiv.className = "message bot loading";
  loadingDiv.innerHTML = `
    <div class="message-avatar">🤖</div>
    <div class="message-content">
      <div class="typing-indicator">
        <span></span>
        <span></span>
        <span></span>
      </div>
      <span>SUNABOT está pensando...</span>
    </div>
  `;
  chatContent.appendChild(loadingDiv);
  
  // Scroll automático
  chatContent.scrollTop = chatContent.scrollHeight;
  
  // Enviar a Google Gemini via endpoint /chat_directo
  fetch("/chat_directo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mensaje: mensaje })
  })
  .then(response => response.json())
  .then(data => {
    // Remover indicador de carga
    loadingDiv.remove();
    
    // Procesar respuesta con markdown
    const processedResponse = processMarkdown(data.respuesta);
    
    // Crear mensaje de respuesta
    const botDiv = document.createElement("div");
    botDiv.className = "message bot";
    botDiv.innerHTML = `
      <div class="message-avatar">🤖</div>
      <div class="message-content">${processedResponse}</div>
      <div class="message-actions">
        <button class="action-btn speak-btn" onclick="speakText(this)" title="Leer respuesta">
          🔊
        </button>
        <button class="action-btn copy-btn" onclick="copyToClipboard(this)" title="Copiar respuesta">
          📋
        </button>
        <button class="action-btn continue-btn" onclick="continueResponse(this)" title="Continuar respuesta">
          ➕
        </button>
        <button class="action-btn retry-btn" onclick="retryLastMessage()" title="Reintentar consulta">
          🔄
        </button>
      </div>
    `;
    
    chatContent.appendChild(botDiv);
    
    // Scroll automático
    chatContent.scrollTop = chatContent.scrollHeight;
    
    // Mostrar indicador de que es IA real
    if (data.calidad === "premium_gemini") {
      console.log("✅ Respuesta generada por IA");
    }
  })
  .catch(error => {
    // Remover indicador de carga
    loadingDiv.remove();
    
    // Mostrar error
    const errorDiv = document.createElement("div");
    errorDiv.className = "message bot error";
    errorDiv.innerHTML = `
      <div class="message-avatar">🤖</div>
      <div class="message-content">
        <span style="color: #f44336;">❌ Error al procesar tu consulta. Por favor, intenta nuevamente.</span>
        <br><br>
        <button class="action-btn retry-btn" onclick="retryLastMessage()" title="Reintentar consulta">
          🔄 Reintentar
        </button>
      </div>
    `;
    chatContent.appendChild(errorDiv);
    chatContent.scrollTop = chatContent.scrollHeight;
    
    console.error("Error:", error);
  });
}

// Función auxiliar para copiar al portapapeles
function copyToClipboard(button) {
  const messageContent = button.closest('.message').querySelector('.message-content');
  const textToCopy = messageContent.innerText || messageContent.textContent;
  
  navigator.clipboard.writeText(textToCopy).then(() => {
    // Cambiar icono temporalmente para mostrar éxito
    const originalText = button.innerHTML;
    button.innerHTML = '✅';
    button.style.color = '#4caf50';
    
    setTimeout(() => {
      button.innerHTML = originalText;
      button.style.color = '';
    }, 2000);
  }).catch(err => {
    console.error('Error al copiar:', err);
    alert('No se pudo copiar el texto');
  });
}

function sendMessage() {
  const input = document.getElementById("userInput");
  const chatbox = document.getElementById("chatbox");
  const mensaje = input.value.trim();

  if (!mensaje) return;

  // Cuando el usuario escribe directamente, SIEMPRE usar GitHub Copilot directo
  sendMessageToBot(mensaje, "chat_directo", null, "copilot");
}

function sendCategoryMessage(categoria, mensajePredefinido) {
  const input = document.getElementById("userInput");
  const mensaje = input.value.trim() || mensajePredefinido;
  
  // Para categorías, usar el sistema de runnables (local)
  sendMessageToBot(mensaje, "categoria", categoria, "local");
}

function showCategoryQuestions(categoria) {
  const chatContent = document.getElementById("chat-content");

  const existingQuestions = chatContent.querySelectorAll('.predefined-questions');
  existingQuestions.forEach(q => q.closest('.message').remove());
  
  const preguntasPredeterminadas = {
    "RUC": [
      "¿Cómo me inscribo en el RUC?",
      "¿Qué documentos necesito para el RUC?", 
      "¿Cómo consulto un RUC?",
      "¿Cómo actualizo mi información en el RUC?"
    ],
    "Declaraciones": [
      "¿Cómo presento mi declaración mensual?",
      "¿Cuáles son las fechas de vencimiento?",
      "¿Cómo consulto mi cronograma de obligaciones?",
      "¿Cómo rectificar mi declaración?"
    ],
    "Facturación": [
      "¿Cómo emito facturas electrónicas?",
      "¿Cómo verifico un comprobante electrónico?",
      "¿Qué tipos de comprobantes existen?",
      "¿Cómo autorizo la impresión de comprobantes?"
    ],
    "Clave SOL": [
      "¿Cómo obtengo mi Clave SOL?",
      "¿Cómo recupero mi contraseña?",
      "¿Cómo accedo a SOL?",
      "¿Dónde está el login de Clave SOL?"
    ],
    "Regímenes": [
      "¿Qué régimen tributario me conviene?",
      "¿Cómo cambio de régimen?",
      "¿Cuáles son las diferencias entre regímenes?"
    ],
    "Otros": [
      "¿Qué infracciones tributarias existen?",
      "¿Qué beneficios tributarios hay?",
      "¿Cómo consulto mi deuda tributaria?"
    ]
  };

  const preguntas = preguntasPredeterminadas[categoria] || [];
  
  const questionsDiv = document.createElement("div");
  questionsDiv.className = "message bot";
  questionsDiv.innerHTML = `
    <div class="message-avatar">🤖</div>
    <div class="message-content">
      <div class="predefined-questions">
        <button class="close-questions" onclick="closeQuestions(this)">×</button>
        <h4>Preguntas frecuentes sobre ${categoria}:</h4>
        ${preguntas.map(pregunta => 
          `<div class="question-item" onclick="selectPredefinedQuestion('${categoria}', '${pregunta.replace(/[📋📄🔄📊📅✏️🧾📑🖨️🔑🔓💻⚖️🔄📊⚠️🎁💰]/g, '').trim()}')">${pregunta}</div>`
        ).join('')}
      </div>
    </div>
  `;
  
  chatContent.appendChild(questionsDiv);
  chatContent.scrollTop = chatContent.scrollHeight;
}

function closeQuestions(button) {
  const messageDiv = button.closest('.message');
  messageDiv.remove();
}

function selectPredefinedQuestion(categoria, pregunta) {
  const questionsDiv = document.querySelector('.predefined-questions').closest('.message');
  questionsDiv.remove();
  sendPredefinedAnswer(categoria, pregunta);
}

function sendPredefinedAnswer(categoria, pregunta) {
  const input = document.getElementById("userInput");
  const chatContent = document.getElementById("chat-content");
  const userDiv = document.createElement("div");
  userDiv.className = "message user";
  userDiv.innerHTML = `
    <div class="message-avatar">👤</div>
    <div class="message-content">${pregunta}</div>
  `;
  chatContent.appendChild(userDiv);

  const respuestasPredeterminadas = {
    "RUC": {
      "¿Cómo me inscribo en el RUC?": `
        **📋 Inscripción al RUC**

        **Pasos para inscribirse:**
        1. Acudir a cualquier centro de servicios SUNAT
        2. Presentar documento de identidad original
        3. Llenar el formulario de inscripción
        4. Proporcionar información de la actividad económica

        **Documentos necesarios:**
        - DNI original y vigente
        - Recibo de servicios (luz, agua, teléfono)
        - Contrato de alquiler (si es inquilino)

        **Tiempo de trámite:** Inmediato
        **Costo:** Gratuito

        **Enlace útil:**
        [Registro de RUC (para nuevos contribuyentes)](https://ww1.sunat.gob.pe/a/html/contribuyente2/registro/adminforuc/registroruc/registroruc.html)
      `,
      "¿Qué documentos necesito para el RUC?": `
        **Documentos para RUC**

        **Persona Natural:**
        - DNI original y vigente
        - Recibo de servicios públicos
        - Contrato de alquiler (si aplica)

        **Persona Jurídica:**
        - Testimonio de escritura pública
        - DNI del representante legal
        - Vigencia de poder del representante
        - Recibo de servicios del domicilio fiscal

        **Notas importantes:**
        - Todos los documentos deben estar vigentes
        - No se aceptan fotocopias
      `,
      "¿Cómo consulto un RUC?": `
        **Consulta de RUC**

        **Pasos para consultar:**
        1. Accede al portal de SUNAT
        2. Ingresa el número de RUC o nombre
        3. Verifica la información del contribuyente

        **Enlace útil:**
        [Consulta de RUC](https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp)
      `,
      "¿Cómo actualizo mi información en el RUC?": `
        **Actualización de Datos RUC**

        **Formas de actualizar:**
        1. **Presencial:** En centros de servicios SUNAT
        2. **Virtual:** A través de SUNAT Operaciones en Línea
        3. **Formularios:** PDT 621

        **Datos que puedes actualizar:**
        - Domicilio fiscal
        - Actividad económica
        - Teléfonos y correos
        - Estado del contribuyente

        **Plazo:** Dentro de los 30 días calendarios del cambio
      `
    },
    "Declaraciones": {
      "¿Cómo presento mi declaración mensual?": `
        **Declaración Jurada Mensual**

        **Pasos para declarar:**
        1. Ingresar a SUNAT Operaciones en Línea (SOL)
        2. Seleccionar "Declaración y Pago"
        3. Elegir el formulario correspondiente
        4. Completar la información tributaria
        5. Generar orden de pago

        **Formularios principales:**
        - **PDT 621:** IGV - Renta Mensual
        - **Formulario Virtual 621:** Más práctico

        **Importante:** Declarar aunque no tengas ventas
      `,
      "¿Cuáles son las fechas de vencimiento?": `
        **Cronograma de Vencimientos**

        **Según último dígito del RUC:**
        - **0 y 1:** 12 del mes siguiente
        - **2 y 3:** 13 del mes siguiente
        - **4 y 5:** 14 del mes siguiente
        - **6 y 7:** 15 del mes siguiente
        - **8 y 9:** 16 del mes siguiente

        **Notas:**
        - Si la fecha cae en feriado, se extiende al día hábil siguiente
        - Principales Contribuyentes tienen fechas diferentes
      `,
      "¿Cómo consulto mi cronograma de obligaciones?": `
        **Cronograma de Obligaciones Tributarias**

        **Consulta tu cronograma:**
        [Cronograma de Obligaciones Tributarias](https://ww3.sunat.gob.pe/cl-ti-itcronobligme/fvS01Alias)
      `,
      "¿Cómo rectificar mi declaración?": `
        **Rectificación de Declaraciones**

        **Cuándo rectificar:**
        - Error en montos declarados
        - Omisión de información
        - Datos incorrectos

        **Cómo rectificar:**
        1. Ingresar a SOL
        2. Ir a "Declaración y Pago"
        3. Seleccionar "Rectificar"
        4. Elegir el período a rectificar
        5. Corregir la información

        **Importante:** Puedes rectificar dentro de los 4 años
      `
    },
    "Facturación": {
      "¿Cómo emito facturas electrónicas?": `
        **Facturación Electrónica**

        **Sistemas disponibles:**
        1. **SEE SUNAT:** Sistema gratuito de SUNAT
        2. **PSE:** Proveedores de Servicios Electrónicos
        3. **Facturador gratuito:** Para pequeñas empresas

        **Pasos básicos:**
        1. Afiliarse al sistema elegido
        2. Configurar datos de la empresa
        3. Emitir comprobantes
        4. Enviar a SUNAT automáticamente

        **Ventajas:** Ahorro de papel, envío automático, respaldo digital
      `,
      "¿Cómo verifico un comprobante electrónico?": `
        **Verificación de Comprobantes Electrónicos (CPE)**

        **Pasos para validar:**
        1. Accede al enlace oficial
        2. Ingresa el número de comprobante
        3. Verifica la validez del documento

        **Enlace útil:**
        [Verificación de Comprobantes Electrónicos](https://e-consulta.sunat.gob.pe/ol-ti-itconsvalicpe/ConsValiCpe.htm)
      `,
      "¿Qué tipos de comprobantes existen?": `
        **Tipos de Comprobantes de Pago**

        **Principales comprobantes:**
        - **Factura:** Para empresas con RUC
        - **Boleta de venta:** Para consumidores finales
        - **Nota de crédito:** Para anular o modificar
        - **Nota de débito:** Para cargos adicionales
        - **Recibo por honorarios:** Para servicios profesionales

        **Comprobantes especiales:**
        - Guía de remisión
        - Ticket de máquina registradora
        - Comprobante de retención
      `
    },
    "Clave SOL": {
      "¿Cómo obtengo mi Clave SOL?": `
        **Obtener Clave SOL**

        **Requisitos:**
        - Tener RUC activo
        - Documento de identidad vigente

        **Formas de obtener:**
        1. **Presencial:** En centros de servicios SUNAT
        2. **Virtual:** Si tienes firma digital
        3. **Por correo:** Para zonas lejanas

        **Proceso presencial:**
        1. Acudir a centro SUNAT con DNI
        2. Solicitar Clave SOL
        3. Crear contraseña segura
        4. Recibir código de usuario

        **Tiempo:** Inmediato
      `,
      "¿Cómo recupero mi contraseña?": `
        **Recuperar Contraseña SOL**

        **Opciones disponibles:**
        1. **Autogeneración:** Si tienes datos registrados
        2. **Presencial:** En centros SUNAT
        3. **Mesa de partes virtual:** Con firma digital

        **Enlace útil:**
        [Recuperar Clave SOL](https://www.gob.pe/7550-recuperar-la-clave-sol)
      `,
      "¿Cómo accedo a SOL?": `
        **Acceso a SUNAT Operaciones en Línea**

        **Datos necesarios:**
        - Número de RUC
        - Usuario SOL
        - Contraseña

        **Pasos para ingresar:**
        1. Ir a www.sunat.gob.pe
        2. Clic en "SOL"
        3. Ingresar RUC sin guiones
        4. Introducir usuario y contraseña
        5. Resolver captcha si aparece

        **Consejos de seguridad:**
        - Usar siempre el sitio oficial
        - Cerrar sesión al terminar
        - No compartir credenciales
      `
    },
    "Regímenes": {
      "¿Qué régimen tributario me conviene?": `
        **Elección de Régimen Tributario**

        **Regímenes disponibles:**

        **Nuevo RUS:** Hasta S/ 8,000 mensuales
        - Cuota fija mensual
        - Sin libros contables
        - Solo personas naturales

        **Régimen Especial (RER):** Hasta S/ 525,000 anuales  
        - Impuesto 1.5% de ingresos netos
        - Libros simplificados

        **Régimen MYPE:** Sin límite de ingresos
        - Hasta 300 UIT: 1% sobre ingresos netos
        - Más de 300 UIT: coeficiente

        **Régimen General:** Sin límites
        - Impuesto a la Renta 29.5%
        - Libros contables completos
      `,
      "¿Cómo cambio de régimen?": `
        **Cambio de Régimen Tributario**

        **Cuándo puedes cambiar:**
        - Inicio de cada año (enero)
        - Durante el año por exclusión
        - Por superar límites del régimen actual

        **Proceso de cambio:**
        1. Ingresar a SOL
        2. Ir a "Mi RUC y otros registros"
        3. Seleccionar "Régimen tributario"
        4. Elegir nuevo régimen
        5. Confirmar cambio

        **Importante:** 
        - El cambio es irreversible durante el año
        - Evalúa bien antes de decidir
      `,
      "¿Cuáles son las diferencias entre regímenes?": `
        **Comparación de Regímenes**

        | Concepto | Nuevo RUS | RER | MYPE | General |
        |----------|-----------|-----|------|---------|
        | **Límite ingresos** | S/ 96,000 | S/ 525,000 | Sin límite | Sin límite |
        | **Impuesto** | Cuota fija | 1.5% | Variable | 29.5% |
        | **IGV** | Incluido | 18% | 18% | 18% |
        | **Libros** | Ninguno | Simplificados | Según ingresos | Completos |
        | **Trabajadores** | Máx. 1 | Sin límite | Sin límite | Sin límite |

        **Recomendación:** Elegir según volumen de ventas y complejidad del negocio
      `
    },
    "Otros": {
      "¿Qué infracciones tributarias existen?": `
        **Infracciones Tributarias**

        **Principales infracciones:**

        **Relacionadas al RUC:**
        - No inscribirse en el RUC
        - No actualizar datos
        - No comunicar cambios

        **Relacionadas a declaraciones:**
        - No presentar declaraciones
        - Presentar con datos incorrectos
        - Presentar fuera de plazo

        **Relacionadas a comprobantes:**
        - No emitir comprobantes
        - Emitir sin requisitos
        - No entregar al adquirente

        **Sanciones:** Multas según tabla de infracciones y sanciones
      `,
      "¿Qué beneficios tributarios hay?": `
        **Beneficios Tributarios**

        **Para nuevas empresas:**
        - Régimen MYPE Tributario
        - Depreciación acelerada
        - Deducción de gastos de constitución

        **Por ubicación geográfica:**
        - Ley de la Amazonía
        - Zonas alto andinas
        - Frontera

        **Sectores específicos:**
        - Agrario
        - Investigación y desarrollo
        - Exportación

        **Para trabajadores:**
        - Deducción por alquiler
        - Gastos médicos
        - Donaciones
      `,
      "¿Cómo consulto mi deuda tributaria?": `
        **Consulta de Deuda Tributaria**

        **Formas de consultar:**
        1. **SOL:** Opción más completa
        2. **Página web SUNAT:** Consulta rápida
        3. **Centros de servicio:** Atención presencial
        4. **App SUNAT:** Desde móvil

        **En SOL:**
        1. Ingresar con Clave SOL
        2. Ir a "Consultas" > "Estado de cuenta"
        3. Seleccionar período
        4. Ver detalle de deudas

        **Información disponible:**
        - Monto de deuda
        - Conceptos adeudados
        - Fechas de vencimiento
        - Intereses y multas
      `
    }
  };

  const respuesta = respuestasPredeterminadas[categoria]?.[pregunta] || 
    `Lo siento, no tengo una respuesta predeterminada para esa pregunta. Por favor, escribe tu consulta en el chat para obtener una respuesta personalizada.`;

  const botDiv = document.createElement("div");
  botDiv.className = "message bot";
  botDiv.innerHTML = `
    <div class="message-avatar">🤖</div>
    <div class="message-content">
      <span class="category-badge">${categoria}</span>
      ${processMarkdown(respuesta)}
      <div class="message-actions">
        <button class="speak-btn" onclick="speakText(this)" title="Escuchar respuesta">🔊</button>
      </div>
    </div>
  `;
  
  chatContent.appendChild(botDiv);
  chatContent.scrollTop = chatContent.scrollHeight;
}

function sendMessageToBot(mensaje, tipo = "general", categoria = null, aiMode = "local") {
  const input = document.getElementById("userInput");
  const chatContent = document.getElementById("chat-content");

  if (currentSpeech || speechSynthesis.speaking) {
    stopCurrentSpeech();
  }
  
  const allSpeechControls = document.querySelectorAll('.speech-control');
  allSpeechControls.forEach(btn => btn.remove());
  
  const allSpeakButtons = document.querySelectorAll('.speak-btn');
  allSpeakButtons.forEach(btn => {
    btn.innerHTML = '🔊';
    btn.title = 'Escuchar respuesta';
    btn.classList.remove('speaking');
  });

  const userDiv = document.createElement("div");
  userDiv.className = "message user";
  userDiv.innerHTML = `
    <div class="message-avatar">👤</div>
    <div class="message-content">${mensaje}</div>
  `;
  chatContent.appendChild(userDiv);

  const botDiv = document.createElement("div");
  botDiv.className = "message bot";
  
  let loadingMessage = "Analizando consulta...";
  if (tipo === "chat_directo") {
    loadingMessage = "⚡respondiendo...";
  } else if (aiMode === "copilot") {
    loadingMessage = "⚡procesando...";
  } else if (tipo === "categoria" && categoria) {
    loadingMessage = `Procesando consulta de ${categoria}...`;
  }
  
  botDiv.innerHTML = `
    <div class="message-avatar">${tipo === "chat_directo" || aiMode === "copilot" ? "⚡" : "🤖"}</div>
    <div class="message-content typing-indicator">
      <span class="typing-dots">
        <span></span>
        <span></span>
        <span></span>
      </span>
      ${loadingMessage}
    </div>
  `;
  chatContent.appendChild(botDiv);

  input.value = "";

  chatContent.scrollTop = chatContent.scrollHeight;

  const requestData = { 
    mensaje: mensaje,
    tipo: tipo,
    max_length: 1500
  };
  
  if (categoria) {
    requestData.categoria = categoria;
  }

  // Seleccionar el endpoint según el tipo de consulta
  let endpoint = "/responder";
  if (tipo === "chat_directo") {
    endpoint = "/chat_directo";
  } else if (aiMode === "copilot") {
    endpoint = "/responder_copilot";
  }

  fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(requestData)
  })
  .then(res => {
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  })
  .then(data => {
    const processedResponse = processMarkdown(data.respuesta);
    
    const isComplete = data.respuesta.length > 30 && 
                      !data.respuesta.endsWith('...') && 
                      !data.respuesta.match(/\b(se|que|la|el|y|o|a|en|de|con|para|por|como|sobre|pero|sin|más|muy|puede|debe|tiene)\s*$/i);
    
    let categoryBadge = '';
    if (data.categoria && data.categoria !== 'Otros') {
      categoryBadge = `<span class="category-badge">${data.categoria}</span>`;
    }

    // Mostrar badge de calidad si es Copilot o Chat Directo
    let qualityBadge = '';
    if (tipo === "chat_directo") {
      //qualityBadge = `<span class="quality-badge"></span>`;
    } else if (aiMode === "copilot") {
      qualityBadge = `<span class="quality-badge">⚡ Premium Quality</span>`;
    }
    
    botDiv.innerHTML = `
      <div class="message-avatar">${tipo === "chat_directo" || aiMode === "copilot" ? "⚡" : "🤖"}</div>
      <div class="message-content">
        ${categoryBadge}
        ${qualityBadge}
        ${processedResponse}
        <div class="message-actions">
          <button class="speak-btn" onclick="speakText(this)" title="Escuchar respuesta">🔊</button>
          ${!isComplete ? '<button class="continue-btn" onclick="continueResponse(this)">Continuar respuesta</button>' : ''}
        </div>
      </div>
    `;
    chatContent.scrollTop = chatContent.scrollHeight;
  })
  .catch(err => {
    let errorMessage = 'Error al procesar la consulta.';
    
    if (err.message.includes('HTTP')) {
      errorMessage = 'Error de conexión con el servidor. <button class="retry-btn" onclick="retryLastMessage()">🔄 Reintentar</button>';
    }
    
    botDiv.innerHTML = `
      <div class="message-avatar">🤖</div>
      <div class="message-content">
        <span style="color: #f44336;">${errorMessage}</span>
      </div>
    `;
  });

  input.value = "";
  window.lastMessage = mensaje;
}


function continueResponse(button) {
  const messageContent = button.closest('.message-content');
  const chatbox = document.getElementById("chatbox");
  
  const continueDiv = document.createElement("div");
  continueDiv.className = "message bot";
  continueDiv.innerHTML = `
    <div class="message-avatar">🤖</div>
    <div class="message-content typing-indicator">
      <span class="typing-dots">
        <span></span>
        <span></span>
        <span></span>
      </span>
      Continuando respuesta...
    </div>
  `;
  chatbox.appendChild(continueDiv);
  chatbox.scrollTop = chatbox.scrollHeight;
  
  button.style.display = 'none';
  
  fetch("/continuar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
      mensaje: "Continúa la respuesta anterior",
      context: messageContent.innerText
    })
  })
  .then(res => res.json())
  .then(data => {
    const processedResponse = processMarkdown(data.respuesta);
    continueDiv.innerHTML = `
      <div class="message-avatar">🤖</div>
      <div class="message-content">${processedResponse}</div>
    `;
    chatbox.scrollTop = chatbox.scrollHeight;
  })
  .catch(err => {
    continueDiv.innerHTML = `
      <div class="message-avatar">🤖</div>
      <div class="message-content">
        <span style="color: #f44336;">Error al continuar la respuesta.</span>
      </div>
    `;
  });
}

function retryLastMessage() {
  if (window.lastMessage) {
    document.getElementById("userInput").value = window.lastMessage;
    sendMessage();
  }
}

document.getElementById("userInput").addEventListener("keypress", function(e) {
  if (e.key === "Enter") {
    sendMessage();
  }
});

let typingTimer;
document.getElementById("userInput").addEventListener("input", function() {
  clearTimeout(typingTimer);
});

document.addEventListener('DOMContentLoaded', function() {
  const categoryButtons = document.querySelector('.category-buttons');
  const chatContent = document.getElementById('chat-content');
  
  if (categoryButtons && chatContent) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          categoryButtons.classList.remove('floating');
        } else {
          categoryButtons.classList.add('floating');
        }
      });
    });
    
    observer.observe(categoryButtons);
  }
});

function smoothScrollToBottom(container) {
  if (container) {
    container.scrollTo({
      top: container.scrollHeight,
      behavior: 'smooth'
    });
  }
}
