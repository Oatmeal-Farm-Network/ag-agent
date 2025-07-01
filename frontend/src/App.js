import { useState, useEffect, useRef } from 'react';
import { Plus, Send, ChevronDown, ChevronUp, X, Mic } from 'lucide-react';
// --- FIX 1: ADD THIS VALIDATION AT THE TOP OF YOUR FILE ---
// This guard clause will cause the app to crash on startup if the environment
// variable is missing in a production environment, preventing silent failures.
if (process.env.NODE_ENV === 'production' && !process.env.REACT_APP_BACKEND_HOST) {
  throw new Error("FATAL: REACT_APP_BACKEND_HOST environment variable is not set for the production build.");
}
// --- START: TEXT-TO-SPEECH INTEGRATION ---

// 1. Reusable Speaker Icon SVG Component
const SpeakerIcon = ({ isSpeaking, onClick }) => (
    <svg 
        onClick={onClick} 
        className={`w-5 h-5 cursor-pointer transition-colors duration-200 ${isSpeaking ? 'text-blue-400' : 'text-gray-400 hover:text-white'}`} 
        xmlns="http://www.w3.org/2000/svg" 
        fill="none" 
        viewBox="0 0 24 24" 
        strokeWidth="1.5" 
        stroke="currentColor"
    >
        <path strokeLinecap="round" strokeLinejoin="round" d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z" />
    </svg>
);

// 2. Custom Hook for Speech Synthesis
const useSpeechSynthesis = () => {
    const [speakingMessageId, setSpeakingMessageId] = useState(null);
    const synth = useRef(window.speechSynthesis);

    const handleSpeak = (message) => {
        const { id, text } = message;

        if (!text) {
            console.error("No text provided to speak.");
            return;
        }

        if (synth.current.speaking && speakingMessageId === id) {
            synth.current.cancel();
            setSpeakingMessageId(null);
            return;
        }

        if (synth.current.speaking) {
            synth.current.cancel();
        }

        const utterance = new SpeechSynthesisUtterance(text);
        
        utterance.onstart = () => {
            setSpeakingMessageId(id);
        };

        utterance.onend = () => {
            setSpeakingMessageId(null);
        };
        
        utterance.onerror = (event) => {
            console.error('SpeechSynthesisUtterance.onerror', event);
            setSpeakingMessageId(null);
        };

        synth.current.speak(utterance);
    };

    useEffect(() => {
        const currentSynth = synth.current;
        return () => {
            if (currentSynth?.speaking) {
                currentSynth.cancel();
            }
        };
    }, []);

    return { speakingMessageId, handleSpeak };
};

// --- END: TEXT-TO-SPEECH INTEGRATION ---
// Helper Components
const AGENT_EMOJIS = {
  "SemanticSearcher": "🔍",
  "ContextProcessor": "📋",
  "SoilScienceSpecialist": "🌱",
  "PlantNutritionExpert": "🧪",
  "LeadAgriculturalAdvisor": "👨‍🌾",
  "WeatherAgent": "🌦️",
  "LivestockBreedAgent": "🐄",
  "default": "🤖"
};

// Modified ChatMessage Component for new layout(for adding speaker option)
const ChatMessage = ({ message, onSpeak, isSpeaking }) => {
  const isAi = message.sender === 'ai';
  return (
    // CHANGE 1: The container for AI messages is now a column (`flex-col`) and aligns items to the start (left).
    // User messages still justify to the end (right).
    <div className={`flex mb-4 ${isAi ? 'flex-col items-start' : 'justify-end'}`}>
      <div 
        className={`rounded-lg px-4 py-2 max-w-2xl shadow-md ${isAi ? 'bg-gray-700 text-white' : 'bg-blue-600 text-white'}`}
      >
        {message.images && message.images.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-2">
            {message.images.map((img, index) => (
              <img 
                key={index}
                src={img.preview} 
                alt={`Uploaded image ${index + 1}`}
                className="max-w-32 max-h-32 object-cover rounded"
              />
            ))}
          </div>
        )}
        
        {message.text && (
          <p className="whitespace-pre-wrap">{message.text}</p>
        )}
      </div>

      {/* CHANGE 2: This block is now a separate row for icons that appears *below* the AI message bubble. */}
      {isAi && message.text && (
          <div className="flex items-center gap-3 mt-2">
              <SpeakerIcon isSpeaking={isSpeaking} onClick={() => onSpeak(message)} />
              
          </div>
      )}
    </div>
  );
};
const ThinkingProcess = ({ steps, isExpanded, setIsExpanded }) => {
  if (steps.length === 0) return null;

  return (
    <div className="flex justify-center mb-4">
      <div className="w-full max-w-2xl bg-gray-800 bg-opacity-50 rounded-lg p-3">
        <button 
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex justify-between items-center text-gray-300 hover:text-white"
        >
          <span>Consulting Experts...</span>
          {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </button>
        {isExpanded && (
          <div className="mt-3 border-t border-gray-600 pt-3 space-y-2">
            {steps.map(step => (
              <div key={step.id} className="text-sm text-gray-400 flex items-start animate-pulse">
                <span className="mr-2">{AGENT_EMOJIS[step.agent_name] || AGENT_EMOJIS.default}</span>
                <span><strong>{step.agent_name}</strong> is working...</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Connection Status Component
const ConnectionStatus = ({ isConnected, isConnecting }) => {
  if (isConnected) return null;
  
  return (
    <div className="flex justify-center mb-4">
      <div className="bg-yellow-600 bg-opacity-80 text-white px-4 py-2 rounded-lg text-sm">
        {isConnecting ? "Connecting to server..." : "⚠️ Connection lost. Attempting to reconnect..."}
      </div>
    </div>
  );
};


// Main App Component
function App() {
  const [messages, setMessages] = useState([
    { id: 1, text: "Hello! I am your agricultural advisor. How can I help you today?", sender: "ai" },
  ]);
  const [thinkingSteps, setThinkingSteps] = useState([]);
  const [isThinking, setIsThinking] = useState(false);
  const [isThinkingExpanded, setIsThinkingExpanded] = useState(false);
  const [input, setInput] = useState('');
  const [selectedImages, setSelectedImages] = useState([]);
  const [imageLimitError, setImageLimitError] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);

    // CALL THE HOOK TO GET THE SPEECH FUNCTIONS ---
  const { speakingMessageId, handleSpeak } = useSpeechSynthesis();
  
  const fileInputRef = useRef(null);
  const socket = useRef(null);
  const chatEndRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  useEffect(() => {
    connect();
    return () => {
      if (socket.current) {
        socket.current.close(1000, "Component unmounting");
      }
    };
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinkingSteps]);

  // IMPROVED: WebSocket connection function with better Azure support
  
  const connect = () => {
    if (socket.current?.readyState === WebSocket.CONNECTING) {
      console.log("WebSocket already connecting...");
      return;
    }

    setIsConnecting(true);

    // Get the backend host. The || 'localhost:8000' fallback is now safe
    // because the guard clause above protects the production environment.
    const backendHost = process.env.REACT_APP_BACKEND_HOST || 'localhost:8000';
    
    // This protocol detection is robust. It checks if the page itself is
    // served over https, which is true for production and optional for local dev.
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    
    // The URL construction is now simplified and no longer makes incorrect
    // assumptions about localhost. It uniformly applies the correct protocol.
    const wsUrl = `${protocol}//${backendHost}/ws/chat`;
    
    console.log(`🔌 Connecting to WebSocket: ${wsUrl}`);
    console.log(`📍 Current location: ${window.location.href}`);

    try {
        socket.current = new WebSocket(wsUrl);

        socket.current.onopen = () => {
            console.log("✅ WebSocket connected successfully!");
            setIsConnected(true);
            setIsConnecting(false);
            reconnectAttempts.current = 0;
        };
      
      socket.current.onclose = (event) => {
        console.log(`🔌 WebSocket closed: Code ${event.code}, Reason: ${event.reason}`);
        setIsConnected(false);
        setIsConnecting(false);
        
        // Reset thinking state if connection is lost
        setIsThinking(false);
        setThinkingSteps([]);
        
        // Attempt reconnection for unexpected closures
        if (event.code !== 1000 && event.code !== 1001 && reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000);
          console.log(`🔄 Attempting reconnection ${reconnectAttempts.current + 1}/${maxReconnectAttempts} in ${delay}ms...`);
          
          setTimeout(() => {
            if (socket.current?.readyState === WebSocket.CLOSED) {
              reconnectAttempts.current++;
              connect();
            }
          }, delay);
        } else if (reconnectAttempts.current >= maxReconnectAttempts) {
          console.error("❌ Max reconnection attempts reached");
          setMessages(prev => [...prev, { 
            id: Date.now(), 
            text: "Connection lost. Please refresh the page to reconnect.", 
            sender: 'ai' 
          }]);
        }
      };

      socket.current.onerror = (error) => {
        console.error("❌ WebSocket error:", error);
        setIsConnecting(false);
        
        // Additional debugging information
        console.log("🐛 Debug info:", {
          readyState: socket.current?.readyState,
          url: wsUrl,
          location: window.location.href,
          userAgent: navigator.userAgent
        });
      };

      socket.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("📨 Received:", data);
          
          switch (data.type) {
            case 'agent_step':
              setIsThinking(true);
              setThinkingSteps(prev => [...prev, { agent_name: data.agent_name, id: Date.now() }]);
              break;
              
            case 'final_answer':
              setMessages(prev => [...prev, { id: Date.now(), text: data.content, sender: 'ai' }]);
              setTimeout(() => {
                setIsThinking(false);
                setIsThinkingExpanded(false);
                setThinkingSteps([]);
              }, 500);
              break;
              
            case 'error':
              setMessages(prev => [...prev, { id: Date.now(), text: data.content, sender: 'ai' }]);
              setIsThinking(false);
              setIsThinkingExpanded(false);
              setThinkingSteps([]);
              break;

            case 'clear_agent_status':
              setThinkingSteps([]);
              break;
              
            default:
              console.warn("❓ Unknown message type:", data.type);
          }
        } catch (error) {
          console.error("❌ Error parsing WebSocket message:", error);
        }
      };
      
    } catch (error) {
      console.error("❌ Error creating WebSocket:", error);
      setIsConnecting(false);
    }
  };
  
  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;
    
    if (selectedImages.length + files.length > 5) {
      setImageLimitError('You can only upload up to 5 images at a time.');
      setTimeout(() => setImageLimitError(''), 3000);
      return;
    }
    
    const newImages = files.map(file => ({
      id: Date.now() + Math.random(),
      file,
      preview: URL.createObjectURL(file)
    }));
    
    setSelectedImages(prev => [...prev, ...newImages]);
    event.target.value = '';
  };
  
  const removeImage = (id) => {
    setSelectedImages(prev => {
      const img = prev.find(img => img.id === id);
      if (img) URL.revokeObjectURL(img.preview);
      return prev.filter(img => img.id !== id);
    });
  };

  const clearAllImages = () => {
    selectedImages.forEach(img => URL.revokeObjectURL(img.preview));
    setSelectedImages([]);
  };

  const handlePlusClick = () => {
    if (selectedImages.length >= 5) {
      setImageLimitError('You can only upload up to 5 images at a time.');
      setTimeout(() => setImageLimitError(''), 3000);
      return;
    }
    fileInputRef.current.click();
  };

  const handleSend = async () => {
    if (isThinking || (!input.trim() && selectedImages.length === 0)) return;
    
    if (!socket.current || socket.current.readyState !== WebSocket.OPEN) {
      console.log("⚠️ WebSocket not connected. Attempting to reconnect...");
      connect();
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        text: "Connection issue detected. Please try again in a moment.", 
        sender: 'ai' 
      }]);
      return;
    }

    try {
      // Convert images to base64
      const imageData = [];
      const messageImages = [];
      
      if (selectedImages.length > 0) {
        for (const img of selectedImages) {
          try {
            const base64 = await fileToBase64(img.file);
            imageData.push({
              name: img.file.name,
              type: img.file.type,
              data: base64
            });
            
            const dataUrl = `data:${img.file.type};base64,${base64}`;
            messageImages.push({
              id: img.id,
              preview: dataUrl
            });
          } catch (error) {
            console.error('❌ Error converting image to base64:', error);
          }
        }
      }

      // Create payload
      const payload = {
        type: "multimodal_query",
        text: input,
        images: imageData,
        user_id: "user123"
      };

      // Display message in UI
      const messageData = {
        id: Date.now(),
        text: input,
        sender: 'user',
        images: messageImages.length > 0 ? messageImages : undefined
      };
      
      setMessages(prev => [...prev, messageData]);

      // Send to backend
      socket.current.send(JSON.stringify(payload));

      setInput('');
      clearAllImages();
      setIsThinking(true);
      setThinkingSteps([]);
      setIsThinkingExpanded(true);
      
    } catch (error) {
      console.error('❌ Error sending message:', error);
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        text: "Error sending message. Please try again.", 
        sender: 'ai' 
      }]);
    }
  };

  // Helper function to convert file to base64
  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = error => reject(error);
    });
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey && !isThinking) {
      event.preventDefault();
      handleSend();
    }
  };

  // --- Audio Recording Logic ---
  const handleMicClick = async () => {
    if (!isRecording) {
      // Start recording
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert('Audio recording is not supported in this browser.');
        return;
      }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const recorder = new window.MediaRecorder(stream, { mimeType: 'audio/webm' });
        let chunks = [];
        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) chunks.push(e.data);
        };
        recorder.onstop = async () => {
          stream.getTracks().forEach(track => track.stop());
          setIsRecording(false);
          setMediaRecorder(null);
          setAudioChunks([]);
          // Convert to blob and send over WebSocket
          const audioBlob = new Blob(chunks, { type: 'audio/webm' });
          const base64 = await blobToBase64(audioBlob);
          if (socket.current && socket.current.readyState === WebSocket.OPEN) {
            socket.current.send(JSON.stringify({
              type: 'audio',
              audio: base64,
              audio_format: 'webm',
              user_id: 'user123'
            }));
          } else {
            setMessages(prev => [
              ...prev,
              { id: Date.now(), text: 'WebSocket not connected. Could not send audio.', sender: 'ai' }
            ]);
          }
        };
        setIsRecording(true);
        setMediaRecorder(recorder);
        setAudioChunks([]);
        recorder.start();
      } catch (err) {
        alert('Could not start audio recording: ' + err.message);
      }
    } else {
      // Stop recording
      if (mediaRecorder) {
        mediaRecorder.stop();
      }
    }
  };

  // Helper: Convert Blob to base64
  const blobToBase64 = (blob) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(blob);
      reader.onloadend = () => {
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
    });
  };

  return (
    <div className="bg-[#131314] h-screen flex flex-col text-white font-sans">
      <header className="p-4 border-b border-gray-700">
        <h1 className="text-xl font-semibold">🌾 Charlie 1.0 - Agricultural Advisor</h1>
      </header>

      <main className="flex-1 overflow-y-auto p-4 md:p-6">
        <div className="max-w-3xl mx-auto">
          <ConnectionStatus isConnected={isConnected} isConnecting={isConnecting} />
          
        
         {messages.map((message) => (
            <ChatMessage 
                key={message.id} 
                message={message} 
                onSpeak={handleSpeak}
                isSpeaking={speakingMessageId === message.id}
            />
          ))}
          <ThinkingProcess 
            steps={thinkingSteps} 
            isExpanded={isThinkingExpanded}
            setIsExpanded={setIsThinkingExpanded}
          />
          
          {/* Recording indicator */}
          {isRecording && (
            <div className="flex justify-center mb-2">
              <div className="bg-red-600 text-white px-4 py-1 rounded-full animate-pulse text-sm">Recording...</div>
            </div>
          )}
          
          <div ref={chatEndRef} />
        </div>
      </main>

      <footer className="p-4 md:p-6">
        <div className="max-w-3xl mx-auto">
          {selectedImages.length > 0 && (
            <div className="mb-2">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">{selectedImages.length} image{selectedImages.length !== 1 ? 's' : ''} uploaded</span>
                <button onClick={clearAllImages} className="text-xs text-red-400 hover:text-red-300 px-2 py-1 rounded">Clear All</button>
              </div>
              <div className="flex flex-wrap gap-2">
                {selectedImages.map(img => (
                  <div key={img.id} className="relative">
                    <img src={img.preview} alt="Preview" className="w-16 h-16 object-cover rounded" />
                    <button
                      onClick={() => removeImage(img.id)}
                      className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center text-xs font-bold transition-colors"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {imageLimitError && (
            <div className="text-xs text-red-400 mb-2">{imageLimitError}</div>
          )}

          <div className="bg-[#1e1f20] rounded-full flex items-center p-2 border border-gray-700">
            <input 
              type="file" 
              ref={fileInputRef}
              onChange={handleFileSelect}
              className="hidden"
              accept="image/*"
              multiple
            />
            <button 
              onClick={handlePlusClick} 
              className="p-2 text-gray-400 hover:text-white rounded-full transition-colors"
              disabled={!isConnected}
            >
              <Plus size={24} />
            </button>
            {/* Mic button: toggles recording */}
            <button
              type="button"
              onClick={handleMicClick}
              className={`p-2 rounded-full transition-colors ${isRecording ? 'bg-red-600 text-white' : 'text-gray-400 hover:text-white'}`}
              aria-label={isRecording ? "Stop recording" : "Start recording"}
              disabled={!isConnected || isThinking}
            >
              <Mic size={24} />
            </button>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder={isConnected ? "Describe your farm problem or ask a follow-up question..." : "Connecting..."}
              className="flex-1 bg-transparent outline-none px-4 text-white placeholder-gray-500"
              disabled={isThinking || !isConnected}
            />
            <button 
              onClick={handleSend}
              className="p-2 text-gray-400 hover:text-white rounded-full transition-colors disabled:opacity-50"
              disabled={(!input.trim() && selectedImages.length === 0) || isThinking || !isConnected}
            >
              <Send size={24} />
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;