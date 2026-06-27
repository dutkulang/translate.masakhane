import { useState, useEffect, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import axios from 'axios';

const languages = [
  { code: 'en', name: 'English' },
  { code: 'sw', name: 'Swahili' },
  { code: 'yo', name: 'Yoruba' },
  { code: 'ha', name: 'Hausa' },
  { code: 'lg', name: 'Luganda' },
];

const Translate = () => {
  const [translation, setTranslation] = useState('');
  const [loading, setLoading] = useState(false);

  const { register, watch, setValue } = useForm({
    defaultValues: {
      fromLang: 'en',
      toLang: 'sw',
      inputText: '',
    },
  });

  const fromLang = watch('fromLang');
  const toLang = watch('toLang');
  const inputText = watch('inputText');

  // Debounced Translation Function
  const debouncedTranslate = useCallback(
    debounce(async (text, sourceLang, targetLang) => {
      if (!text.trim()) {
        setTranslation('');
        return;
      }

      setLoading(true);
      try {
            const response = await axios.post('http://127.0.0.1:8000/translate', {
            text: text.trim(),
            source_lang: sourceLang, // Maps your frontend state to the backend key
            target_lang: targetLang, // Maps your frontend state to the backend key
        });
        setTranslation(response.data.translated_text || "Translation will appear here...");
        
      } catch (error) {
        console.error('Translation error:', error);
        setTranslation("⚠️ Translation service is currently unavailable.");
      } finally {
        setLoading(false);
      }
    }, 800), // 800ms debounce
    []
  );

  // Auto-translate when input changes
  useEffect(() => {
    if (inputText) {
      debouncedTranslate(inputText, fromLang, toLang);
    } else {
      setTranslation('');
    }
  }, [inputText, fromLang, toLang, debouncedTranslate]);

  const swapLanguages = () => {
    setValue('fromLang', toLang);
    setValue('toLang', fromLang);
  };

  const copyTranslation = () => {
    if (translation) {
      navigator.clipboard.writeText(translation);
      alert("✅ Copied to clipboard!");
    }
  };

  const giveFeedback = () => {
    alert("Thank you! Your feedback helps improve Masakhane models.");
  };

  return (
    <div className="bg-[#f8f4eb] min-h-screen text-[#0a4f4a]">
      {/* HERO */}
      <header className="pt-20 pb-16 text-center">
        <div className="max-w-3xl mx-auto px-6">
          <h1 className="text-5xl md:text-6xl font-bold tracking-tight mb-4 text-[#0a4f4a]">
            Masakhane
          </h1>
          <p className="md:text-2xl text-gray-600">
            Machine translation service for African languages
          </p>
        </div>
      </header>

      {/* TRANSLATOR */}
      <div className="max-w-5xl mx-auto px-4 md:px-6 pb-20">
        <div className="bg-white rounded-3xl shadow-xl p-2 md:p-3">
          <div className="bg-[#f0f4f3] rounded-3xl">
            <div className="flex flex-col md:flex-row">
              {/* From */}
              <div className="flex-1 p-6 border-r border-gray-100">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <span className="font-medium">From:</span>
                    <select {...register('fromLang')} className="bg-transparent font-medium focus:outline-none cursor-pointer">
                      {languages.map(lang => (
                        <option key={lang.code} value={lang.code}>{lang.name}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <textarea
                  {...register('inputText')}
                  rows={8}
                  className="w-full bg-transparent focus:outline-none resize-none text-lg placeholder-gray-400"
                  placeholder="Enter text..."
                />
              </div>

              {/* To */}
              <div className="flex-1 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <span className="font-medium">To:</span>
                    <select {...register('toLang')} className="bg-transparent font-medium focus:outline-none cursor-pointer">
                      {languages.map(lang => (
                        <option key={lang.code} value={lang.code}>{lang.name}</option>
                      ))}
                    </select>
                  </div>
                  <button
                    type="button"
                    onClick={swapLanguages}
                    className="text-[#0a4f4a] hover:bg-white p-3 rounded-2xl transition-colors"
                  >
                    <i className="fa-solid fa-arrows-rotate text-xl"></i>
                  </button>
                </div>

                <div className="min-h-[200px] p-6 bg-white rounded-2xl text-lg border">
                  {loading ? (
                    <span className="text-gray-400 italic">Translating...</span>
                  ) : translation ? (
                    translation
                  ) : (
                    <span className="text-gray-400">Translation will appear here in real-time...</span>
                  )}
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-4 justify-between items-center px-6 py-6">
              <button
                type="button"
                onClick={giveFeedback}
                className="border border-gray-300 hover:border-[#0a4f4a] px-6 py-4 rounded-3xl flex items-center gap-2 transition-colors"
              >
                <i className="fa-solid fa-comment-dots"></i>
                Feedback
              </button>

              <button
                onClick={copyTranslation}
                disabled={!translation}
                className="border border-gray-300 hover:border-[#0a4f4a] hover:cursor-pointer px-6 py-4 rounded-3xl flex items-center gap-2 transition-colors disabled:opacity-50"
              >
                <i className="fa-solid fa-copy"></i>
                Copy
              </button>
            </div>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="max-w-3xl mx-auto text-center mt-12 text-sm text-gray-600">
          <p className="mb-4">
            This is a <strong>community research project</strong>. 
            Translations are experimental and may contain errors.
          </p>
          <p>
            Don't see your language?{' '}
            <a href="#" className="text-[#0a4f4a] underline">Learn how to contribute →</a>
          </p>
        </div>
      </div>
    </div>
  );
};

// Debounce Helper Function
function debounce(func, delay) {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
}

export default Translate;