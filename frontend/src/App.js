import React, { useState, useEffect, useRef } from 'react';
import { Plus, Send, ChevronDown, ChevronUp, X, Mic, MessageCircle, Volume2, VolumeX, Sparkles, Loader2 } from 'lucide-react';
// --- FIX 1: ADD THIS VALIDATION AT THE TOP OF YOUR FILE ---
// This guard clause will cause the app to crash on startup if the environment
// variable is missing in a production environment, preventing silent failures.
if (process.env.NODE_ENV === 'production' && !process.env.REACT_APP_BACKEND_HOST) {
  throw new Error("FATAL: REACT_APP_BACKEND_HOST environment variable is not set for the production build.");
}
// --- START: speaker icon INTEGRATION ---

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
    const audioRef = useRef(null);

    const handleSpeak = (message) => {
        const { id, audio } = message;

        // If we're already speaking this message, stop it
        if (speakingMessageId === id) {
            if (audioRef.current) {
                audioRef.current.pause();
                audioRef.current.currentTime = 0;
                audioRef.current = null;
            }
            setSpeakingMessageId(null);
            return;
        }

        // Stop any currently playing audio
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.currentTime = 0;
            audioRef.current = null;
        }

        // Play the audio if available
        if (audio) {
            try {
                let audioElement;
                
                // Check if audio is a base64 string (from backend) or a file path (static file)
                if (audio.includes('data:') || audio.length > 100) {
                    // Base64 audio from backend
                    const audioBlob = new Blob([Uint8Array.from(atob(audio), c => c.charCodeAt(0))], { type: 'audio/wav' });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    audioElement = new Audio(audioUrl);
                    
                    audioElement.onended = () => {
                        setSpeakingMessageId(null);
                        URL.revokeObjectURL(audioUrl);
                        audioRef.current = null;
                    };
                } else {
                    // Static file path
                    audioElement = new Audio(`/welcome-audio.wav`);
                    
                    audioElement.onended = () => {
                        setSpeakingMessageId(null);
                        audioRef.current = null;
                    };
                }
                
                audioRef.current = audioElement;
                
                audioElement.onerror = (error) => {
                    console.error('Error playing audio:', error);
                    setSpeakingMessageId(null);
                    audioRef.current = null;
                };
                
                setSpeakingMessageId(id);
                audioElement.play();
            } catch (error) {
                console.error('Error playing audio:', error);
            }
        }
    };

    useEffect(() => {
        return () => {
            if (audioRef.current) {
                audioRef.current.pause();
                audioRef.current = null;
            }
        };
    }, []);

    return { speakingMessageId, handleSpeak };
};

// --- END: speaker icon  INTEGRATION ---
// Helper Components
const AGENT_EMOJIS = {
  "SemanticSearcher": "🔍",
  "ContextProcessor": "📋",
  "SoilScienceSpecialist": "🌱",
  "PlantNutritionExpert": "🧪",
  "LeadAgriculturalAdvisor": "👨‍🌾",
  "WeatherSpecialist": "🌦️",
  "LivestockBreedSpecialist": "🐄",
  "Farmer_Query_Relay": "👤",
  "default": "🤖"
};


// ChatMessage Component(along with SpeakerIcon)

const ChatMessage = ({ message, onSpeak, isSpeaking }) => {
  const isAi = message.sender === 'ai';
  return (
    // The container for AI messages is a column (`flex-col`)
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

      {/* This block renders the speaker icon below the AI message bubble */}
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

// VoiceChat Component (JavaScript version without framer-motion)
const VoiceChat = React.forwardRef(({ onStart, onStop, onVolumeChange, className, demoMode = true, autoStart = false }, ref) => {
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [volume, setVolume] = useState(0);
  const [waveformData, setWaveformData] = useState(Array(32).fill(0));
  const intervalRef = useRef();
  const mediaRecorderRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const microphoneRef = useRef(null);
  const audioStreamRef = useRef(null);
  const silenceTimerRef = useRef(null);
  const lastVolumeTimeRef = useRef(Date.now());
  const recordingStartTimeRef = useRef(null);

  // Expose methods to parent component
  React.useImperativeHandle(ref, () => ({
    stopListening: () => {
      setIsListening(false);
      stopAudioRecording();
    },
    handleVoiceResponse: (data) => {
      setIsProcessing(false);
      setIsSpeaking(true);
      
      // Play the audio response if available
      if (data.audio) {
        playAudioResponse(data.audio);
      } else {
        // Fallback: use Web Speech API
        speakText(data.text);
      }
    },
    stopAudioPlayback: () => {
      stopAudioPlayback();
    }
  }));

  // Real audio recording and visualization
  useEffect(() => {
    if (isListening) {
      startAudioRecording();
    } else {
      stopAudioRecording();
    }

    return () => {
      stopAudioRecording();
    };
  }, [isListening]);

  const startAudioRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioStreamRef.current = stream; // Store stream reference
      
      // Set up MediaRecorder for recording (but we won't store the data)
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;
      
      // Set up audio analysis for visualization
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      audioContextRef.current = audioContext;
      
      const analyser = audioContext.createAnalyser();
      analyserRef.current = analyser;
      analyser.fftSize = 64;
      
      const microphone = audioContext.createMediaStreamSource(stream);
      microphoneRef.current = microphone;
      microphone.connect(analyser);
      
      // Start recording (data will be discarded)
      mediaRecorder.ondataavailable = (event) => {
        // Discard the audio data - we're just recording for visualization
        console.log('Audio data recorded but discarded');
      };
      
      mediaRecorder.start();
      recordingStartTimeRef.current = Date.now();
      
      // Start visualization
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      intervalRef.current = setInterval(() => {
        analyser.getByteFrequencyData(dataArray);
        
        // Convert frequency data to waveform visualization
        const newWaveform = Array(32).fill(0).map((_, index) => {
          const dataIndex = Math.floor(index * dataArray.length / 32);
          return dataArray[dataIndex] || 0;
        });
        setWaveformData(newWaveform);
        
        // Calculate volume level
        const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
        const volumeLevel = (average / 255) * 100;
        setVolume(volumeLevel);
        onVolumeChange?.(volumeLevel);
        
        // Auto-stop after silence detection with better noise filtering
        const recordingDuration = Date.now() - recordingStartTimeRef.current;
        const minRecordingTime = 2000; // Minimum 2 seconds before auto-stop
        
        if (volumeLevel > 20) { // Higher threshold to filter background noise
          lastVolumeTimeRef.current = Date.now();
          if (silenceTimerRef.current) {
            clearTimeout(silenceTimerRef.current);
            silenceTimerRef.current = null;
          }
        } else if (!silenceTimerRef.current && isListening && recordingDuration > minRecordingTime) {
          // Start silence timer (2.5 seconds of silence) - only after minimum recording time
          silenceTimerRef.current = setTimeout(() => {
            if (isListening) {
              console.log("Auto-stopping due to silence");
              handleToggleListening();
            }
          }, 2500);
        }
      }, 100);
      
      onStart?.();
    } catch (error) {
      console.error('Error starting audio recording:', error);
      // Fallback to simulation if audio recording fails
      startSimulation();
    }
  };

  const stopAudioRecording = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
    }
    
    if (microphoneRef.current) {
      microphoneRef.current.disconnect();
      microphoneRef.current = null;
    }
    
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    // Stop the actual audio stream to clear browser recording indicator
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach(track => {
        track.stop();
        console.log('Audio track stopped:', track.kind);
      });
      audioStreamRef.current = null;
    }
    
    setWaveformData(Array(32).fill(0));
    setVolume(0);
    onStop?.(0);
  };

  const startSimulation = () => {
    intervalRef.current = setInterval(() => {
      // Simulate audio waveform
      const newWaveform = Array(32).fill(0).map(() => 
        Math.random() * (isListening ? 100 : 20)
      );
      setWaveformData(newWaveform);
      
      // Simulate volume changes
      const newVolume = Math.random() * 100;
      setVolume(newVolume);
      onVolumeChange?.(newVolume);
    }, 100);
  };

  // Auto-start listening when component mounts
  useEffect(() => {
    if (autoStart && !demoMode) {
      setIsListening(true);
      onStart?.();
    }
  }, [autoStart, demoMode, onStart]);

  // Demo mode simulation
  useEffect(() => {
    if (!demoMode) return;

    const demoSequence = async () => {
      // Start listening
      setIsListening(true);
      onStart?.();
      
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // Stop listening and start processing
      setIsListening(false);
      setIsProcessing(true);
      onStop?.(0);
      
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Start speaking response
      setIsProcessing(false);
      setIsSpeaking(true);
      
      await new Promise(resolve => setTimeout(resolve, 4000));
      
      // Reset
      setIsSpeaking(false);
      
      // Repeat demo
      setTimeout(demoSequence, 2000);
    };

    const timeout = setTimeout(demoSequence, 1000);
    return () => clearTimeout(timeout);
  }, [demoMode, onStart, onStop]);

  const handleToggleListening = () => {
    if (demoMode) return;
    
    if (isListening) {
      // Stop listening and start processing
      setIsListening(false);
      setIsProcessing(true);
      onStop?.(0);
      
      // Get the recorded audio and send to backend
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
        mediaRecorderRef.current.ondataavailable = async (event) => {
          if (event.data.size > 0) {
            const audioBlob = new Blob([event.data], { type: 'audio/webm' });
            const base64 = await blobToBase64(audioBlob);
            
            // Send to backend for processing
            if (window.socket && window.socket.readyState === WebSocket.OPEN) {
              window.socket.send(JSON.stringify({
                type: 'voice_conversation',
                audio: base64,
                audio_format: 'webm',
                user_id: 'user123'
              }));
            }
          }
        };
      }
    } else {
      setIsListening(true);
      onStart?.();
    }
  };

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

  const audioRef = useRef(null);

  const playAudioResponse = (audioBase64) => {
    try {
      const audioBlob = new Blob([Uint8Array.from(atob(audioBase64), c => c.charCodeAt(0))], { type: 'audio/wav' });
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      
      // Store audio reference for stopping later
      audioRef.current = audio;
      
      audio.onended = () => {
        setIsSpeaking(false);
        URL.revokeObjectURL(audioUrl);
        audioRef.current = null;
      };
      
      audio.onerror = () => {
        console.error('Error playing audio response');
        setIsSpeaking(false);
        URL.revokeObjectURL(audioUrl);
        audioRef.current = null;
      };
      
      audio.play();
    } catch (error) {
      console.error('Error creating audio from base64:', error);
      setIsSpeaking(false);
    }
  };

  const stopAudioPlayback = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    
    // Also stop any speech synthesis
    if ('speechSynthesis' in window) {
      speechSynthesis.cancel();
    }
    
    setIsSpeaking(false);
  };

  const speakText = (text) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);
      speechSynthesis.speak(utterance);
    } else {
      setIsSpeaking(false);
    }
  };

  const getStatusText = () => {
    if (isListening) return "Listening...";
    if (isProcessing) return "Processing...";
    if (isSpeaking) return "Speaking...";
    return "Tap to speak";
  };

  const getStatusColor = () => {
    if (isListening) return "text-blue-400";
    if (isProcessing) return "text-yellow-400";
    if (isSpeaking) return "text-green-400";
    return "text-gray-400";
  };

  // Simulate waveform animation during speaking
  useEffect(() => {
    if (isSpeaking) {
      // Start interval to animate waveform bars
      intervalRef.current = setInterval(() => {
        const newWaveform = Array(32).fill(0).map(() => Math.random() * 80 + 20); // random heights between 20-100
        setWaveformData(newWaveform);
      }, 100);
    } else if (!isListening) {
      // Only clear if not listening (listening has its own interval)
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setWaveformData(Array(32).fill(0));
    }
    // Cleanup on unmount
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isSpeaking, isListening]);

  return (
    <div className={`flex flex-col items-center justify-center min-h-[600px] w-full relative overflow-hidden ${className || ''}`}>
      {/* Background glow effects */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div 
          className={`w-96 h-96 rounded-full bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 blur-3xl transition-all duration-2000 ${
            isListening ? 'scale-110 opacity-60' : 'scale-100 opacity-20'
          }`}
        />
      </div>

      <div className="relative z-10 flex flex-col items-center space-y-8">
        {/* Main voice button */}
        <div className="relative group">
          <button
            onClick={handleToggleListening}
            className={`
              relative w-32 h-32 rounded-full flex items-center justify-center transition-all duration-300
              bg-gradient-to-br from-blue-500/20 to-blue-500/10 border-2
              ${isListening ? 'border-blue-500 shadow-lg shadow-blue-500/25' :
                isProcessing ? 'border-yellow-500 shadow-lg shadow-yellow-500/25' :
                isSpeaking ? 'border-green-500 shadow-lg shadow-green-500/25' :
                'border-gray-600 hover:border-blue-500/50'}
              group-hover:scale-105 active:scale-95
            `}
          >
            {isProcessing ? (
              <Loader2 className="w-12 h-12 text-yellow-500 animate-spin" />
            ) : isSpeaking ? (
              <Volume2 className="w-12 h-12 text-green-500" />
            ) : isListening ? (
              <Mic className="w-12 h-12 text-blue-500" />
            ) : (
              <Mic className="w-12 h-12 text-gray-400" />
            )}
          </button>

          {/* Pulse rings */}
          {isListening && (
            <>
              <div className="absolute inset-0 rounded-full border-2 border-blue-500/30 animate-ping" />
              <div className="absolute inset-0 rounded-full border-2 border-blue-500/20 animate-ping" style={{ animationDelay: '0.5s' }} />
            </>
          )}
        </div>

        {/* Waveform visualizer */}
        <div className="flex items-center justify-center space-x-1 h-16">
          {waveformData.map((height, index) => (
            <div
              key={index}
              className={`
                w-1 rounded-full transition-all duration-100
                ${isListening ? 'bg-blue-500' :
                  isProcessing ? 'bg-yellow-500' :
                  isSpeaking ? 'bg-green-500' :
                  'bg-gray-600'}
              `}
              style={{
                height: `${Math.max(4, height * 0.6)}px`,
                opacity: isListening || isSpeaking ? 1 : 0.3
              }}
            />
          ))}
        </div>

        {/* Status */}
        <div className="text-center space-y-2">
          <p className={`text-lg font-medium transition-colors ${getStatusColor()}`}>
            {getStatusText()}
          </p>
        </div>
      </div>
    </div>
  );
});

// Main App Component
function App() {
  const [messages, setMessages] = useState([
    { id: 1, text: "Hello! I am your agricultural advisor. How can I help you today?", sender: "ai", audio: "welcome-audio.wav" },
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
  const [showConversationModal, setShowConversationModal] = useState(false);
  const [transcribedText, setTranscribedText] = useState('');
  const { speakingMessageId, handleSpeak } = useSpeechSynthesis();
  
  const fileInputRef = useRef(null);
  const socket = useRef(null);
  const chatEndRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const voiceChatRef = useRef(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const inputRef = useRef(null);

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
            // Make socket available globally for VoiceChat component
            window.socket = socket.current;
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
              
            case 'transcribed_audio':
              // Append transcribed text to existing input for user to edit
              setTranscribedText(data.text);
              setInput(prevInput => {
                const separator = prevInput.trim() ? ' ' : '';
                return prevInput + separator + data.text;
              });
              break;
              
            case 'final_answer':
              setMessages(prev => [...prev, { 
                id: Date.now(), 
                text: data.content, 
                sender: 'ai',
                audio: data.audio  // Store the Azure TTS audio
              }]);
              
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

            case 'voice_response':
              // Handle voice conversation response
              console.log("🎤 Voice response received:", data);
              
              // Stop processing and start speaking
              if (voiceChatRef.current) {
                voiceChatRef.current.handleVoiceResponse(data);
              }
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

  // Drag and drop handlers for image upload
  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    const files = Array.from(e.dataTransfer.files).filter(file => file.type.startsWith('image/'));
    if (files.length > 0) {
      // Create a synthetic event to reuse handleFileSelect
      const syntheticEvent = { target: { files } };
      handleFileSelect(syntheticEvent);
    }
  };

  // Auto-resize effect for textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 100) + 'px';
    }
  }, [input]);

  return (
    <div className="bg-[#131314] h-screen flex flex-col text-white font-sans">
      <header className="p-3 md:p-4 border-b border-gray-700">
          <h1 className="text-base sm:text-lg md:text-xl font-semibold truncate">🌾 Charlie 1.0 - Agricultural Advisor</h1>
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
          
              {isThinking && (
                <ThinkingProcess 
                steps={thinkingSteps} 
                isExpanded={isThinkingExpanded}
                setIsExpanded={setIsThinkingExpanded}
              />
              )}
          
          {/* Recording indicator */}
          {isRecording && (
            <div className="flex justify-center mb-2">
              <div className="bg-red-600 text-white px-4 py-1 rounded-full animate-pulse text-sm">Recording...</div>
            </div>
          )}
          
          <div ref={chatEndRef} />
        </div>
      </main>

      {/* --- START: REPLACED FOOTER SECTION --- */}
      <footer className="p-2 md:p-4">
        <div className="max-w-3xl mx-auto">
          {/* Show image limit error above the chatbar */}
          {imageLimitError && (
            <div className="text-xs text-red-400 mb-2">{imageLimitError}</div>
          )}
          {/* Move image preview section above the input bar */}
          {selectedImages.length > 0 && (
            <div className="mb-4">
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
          {/* This container holds the entire new input bar */}
          <div
            className={`bg-[#1e1f20] rounded-xl flex items-center p-2 gap-2 border border-gray-700 ${isDragActive ? 'ring-2 ring-blue-400 border-blue-400' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            {/* 1. The "+" Button (Always visible on the left) */}
            <button 
              onClick={handlePlusClick} 
              className="p-2 text-gray-400 hover:text-white rounded-full transition-colors"
              disabled={!isConnected}
            >
              <Plus size={24} />
            </button>
            {/* Hidden file input, needed for the + button to work */}
            <input 
              type="file" 
              ref={fileInputRef}
              onChange={handleFileSelect}
              className="hidden"
              accept="image/*"
              multiple
            />
            {/* 2. The Text Input (Always visible in the middle) */}
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Describe your farm problem..."
              className="flex-1 bg-transparent outline-none text-white placeholder-gray-500 overflow-auto min-h-[40px] max-h-[120px] py-2"
              disabled={isThinking || !isConnected}
              rows={1}
            />

            {/* 3. CONDITIONAL BUTTONS SECTION */}
            {/* Checks if the input is empty to decide which buttons to show */}
            {input.trim() === '' ? (
              
              // If input is empty, show these action buttons
              <div className="flex items-center">
                <button
                  type="button"
                  onClick={handleMicClick}
                  className={`p-2 rounded-full transition-colors ${isRecording ? 'bg-red-600 text-white' : 'text-gray-400 hover:text-white'}`}
                  aria-label={isRecording ? "Stop recording" : "Start recording"}
                  disabled={!isConnected || isThinking}
                >
                  <Mic size={24} />
                </button>
                <button 
                  className="p-2 text-gray-400 hover:text-white rounded-full transition-colors"
                  title="Conversation (coming soon)"
                  disabled={isThinking || !isConnected}
                  onClick={() => setShowConversationModal(true)}
                >
                  <MessageCircle size={24} />
                </button>
              </div>

            ) : (
              
              // If there is text, show the Send button
              <button 
                onClick={handleSend}
                className="p-2 bg-blue-600 text-white rounded-full transition-colors disabled:opacity-50"
                disabled={isThinking || !isConnected}
              >
                <Send size={24} />
              </button>
            )}
          </div>
        </div>
      </footer>
      {/* --- END: REPLACED FOOTER SECTION --- */}


      {/* Conversation Modal */}
      {showConversationModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60">
          <div className="bg-[#232324] rounded-2xl shadow-2xl p-12 max-w-4xl w-full min-h-[600px] flex flex-col items-center justify-center relative border border-gray-700">
            <button
              className="absolute top-6 right-6 text-gray-400 hover:text-white"
              onClick={() => {
                setShowConversationModal(false);
                // Stop listening and audio playback when modal is closed
                if (voiceChatRef.current) {
                  voiceChatRef.current.stopListening();
                  voiceChatRef.current.stopAudioPlayback();
                }
              }}
              aria-label="Close conversation"
            >
              <X size={32} />
            </button>
            
            {/* Voice Chat Component */}
            <VoiceChat
              ref={voiceChatRef}
              onStart={() => console.log("Voice recording started")}
              onStop={(duration) => console.log(`Voice recording stopped after ${duration}s`)}
              onVolumeChange={(volume) => console.log(`Volume: ${volume}%`)}
              demoMode={false}
              autoStart={true}
            />
          </div>
        </div>
      )}
    </div>
  );
}
export default App;