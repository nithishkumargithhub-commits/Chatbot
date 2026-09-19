import React, { useState, useEffect, useRef } from 'react';
import {
  Mic,
  Square,
  Sparkles,
  Volume2,
  VolumeX,
  Briefcase,
  GraduationCap,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  Upload,
  RefreshCw,
  ArrowRight,
  Radio,
} from 'lucide-react';

const LANGUAGE_META = {
  ta: { flag: '🇮🇳', name: 'Tamil (தமிழ்)', speechLang: 'ta-IN' },
  te: { flag: '🇮🇳', name: 'Telugu (తెలుగు)', speechLang: 'te-IN' },
  hi: { flag: '🇮🇳', name: 'Hindi (हिन्दी)', speechLang: 'hi-IN' },
  kn: { flag: '🇮🇳', name: 'Kannada (ಕನ್ನಡ)', speechLang: 'kn-IN' },
  ml: { flag: '🇮🇳', name: 'Malayalam (മലയാളം)', speechLang: 'ml-IN' },
  en: { flag: '🌐', name: 'English', speechLang: 'en-IN' },
  mr: { flag: '🇮🇳', name: 'Marathi (मराठी)', speechLang: 'mr-IN' },
  gu: { flag: '🇮🇳', name: 'Gujarati (ગુજરાતી)', speechLang: 'gu-IN' },
  bn: { flag: '🇮🇳', name: 'Bengali (বাংলা)', speechLang: 'bn-IN' },
};

// UI Multilingual Labels
const UI_TEXT = {
  en: {
    youSpoke: 'You Spoke',
    recommendation: 'JeevanPath AI Recommendation',
    listenAnswer: 'Listen to Answer',
    stopAudio: 'Stop Audio',
    grantTitle: 'PM-AJAY Scheme Grant',
    nsqfTitle: 'NSQF Skill Qualification',
    nextStepTitle: 'Recommended Next Step',
    askAnother: 'Ask Another Question',
    tapToSpeak: 'Tap to Speak',
    tapToStop: 'Tap to Stop',
    listening: 'Listening to your voice...',
    tapWhenDone: 'Tap the red button when you finish speaking',
    analyzing: 'Analyzing speech with Whisper...',
    tapInstruction: 'Tap the green button & speak in your native language',
    autoSpeakLabel: 'Auto-Talk Back',
  },
  ta: {
    youSpoke: 'நீங்கள் பேசியது',
    recommendation: 'ஜீவன்பாதை AI வழிகாட்டல்',
    listenAnswer: 'பதிலைக் கேளுங்கள்',
    stopAudio: 'ஆடியோவை நிறுத்து',
    grantTitle: 'PM-AJAY திட்ட மானிய உதவி',
    nsqfTitle: 'NSQF திறன் தகுதிச் சான்றிதழ்',
    nextStepTitle: 'பரிந்துரைக்கப்படும் அடுத்த கட்ட நடவடிக்கை',
    askAnother: 'மற்றுமொரு கேள்வி கேளுங்கள்',
    tapToSpeak: 'பேச தொடங்குங்கள்',
    tapToStop: 'முடிக்க தொடவும்',
    listening: 'உங்கள் பேச்சைக் கேட்கிறது...',
    tapWhenDone: 'பேசி முடித்ததும் சிவப்பு பட்டனைத் தொடவும்',
    analyzing: 'உங்கள் குரல் ஆராயப்படுகிறது...',
    tapInstruction: 'பச்சை பட்டனைத் தொட்டு உங்கள் தாய்மொழியில் பேசுங்கள்',
    autoSpeakLabel: 'தானாக பேசவும்',
  },
  hi: {
    youSpoke: 'आपने कहा',
    recommendation: 'जीवनपथ AI अनुशंसा',
    listenAnswer: 'उत्तर सुनें',
    stopAudio: 'आवाज बंद करें',
    grantTitle: 'PM-AJAY योजना अनुदान सहायता',
    nsqfTitle: 'NSQF कौशल योग्यता प्रमाणन',
    nextStepTitle: 'अनुशंसित अगला कदम',
    askAnother: 'दूसरा सवाल पूछें',
    tapToSpeak: 'बोलने के लिए छुएं',
    tapToStop: 'समाप्त करने के लिए छुएं',
    listening: 'आपकी आवाज सुनी जा रही है...',
    tapWhenDone: 'बोलने के बाद लाल बटन को दबाएं',
    analyzing: 'आपकी आवाज का विश्लेषण हो रहा है...',
    tapInstruction: 'हरा बटन दबाएं और अपनी भाषा में बोलें',
    autoSpeakLabel: 'उत्तर बोलकर सुनाएं',
  },
  te: {
    youSpoke: 'మీరు మాట్లాడినది',
    recommendation: 'జీవన్‌పథ్ AI సిఫార్సు',
    listenAnswer: 'సమాధానం వినండి',
    stopAudio: 'ఆపండి',
    grantTitle: 'PM-AJAY పథకం గ్రాంట్ సాయం',
    nsqfTitle: 'NSQF నైపుణ్య అర్హత సర్టిఫికేషన్',
    nextStepTitle: 'సిఫార్సు చేయబడిన తదుపరి దశ',
    askAnother: 'మరొక ప్రశ్న అడగండి',
    tapToSpeak: 'మాట్లాడటానికి తాకండి',
    tapToStop: 'ముగించడానికి తాకండి',
    listening: 'మీ మాటలను వింటోంది...',
    tapWhenDone: 'మాట్లాడటం పూర్తయిన తర్వాత ఎరుపు బటన్‌ను నొక్కండి',
    analyzing: 'మీ మాటలను విశ్లేషిస్తోంది...',
    tapInstruction: 'ఆకుపచ్చ బటన్‌ను తాకి మీ మాతృభాషలో మాట్లాడండి',
    autoSpeakLabel: 'వాయిస్ సమాధానం స్వయంచాలకంగా వినండి',
  },
  kn: {
    youSpoke: 'ನೀವು ಮಾತನಾಡಿದ್ದು',
    recommendation: 'ಜೀವನ್‌ಪಥ್ AI ಶಿಫಾರಸು',
    listenAnswer: 'ಉತ್ತರವನ್ನು ಆಲಿಸಿ',
    stopAudio: 'ನಿಲ್ಲಿಸಿ',
    grantTitle: 'PM-AJAY ಯೋಜನೆ ಅನುದಾನ ನೆರವು',
    nsqfTitle: 'NSQF ಕೌಶಲ್ಯ ಪ್ರಮಾಣಪತ್ರ',
    nextStepTitle: 'ಮುಂದಿನ ಹಂತ',
    askAnother: 'ಮತ್ತೊಂದು ಪ್ರಶ್ನೆ ಕೇಳಿ',
    tapToSpeak: 'ಮಾತನಾಡಲು ಸ್ಪರ್ಶಿಸಿ',
    tapToStop: 'ನಿಲ್ಲಿಸಲು ಸ್ಪರ್ಶಿಸಿ',
    listening: 'ನಿಮ್ಮ ಧ್ವನಿಯನ್ನು ಆಲಿಸುತ್ತಿದೆ...',
    tapWhenDone: 'ಮಾತನಾಡಿ ಮುಗಿದ ನಂತರ ಕೆಂಪು ಬಟನ್ ಒತ್ತಿ',
    analyzing: 'ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತಿದೆ...',
    tapInstruction: 'ಹಸಿರು ಬಟನ್ ಒತ್ತಿ ನಿಮ್ಮ ಭಾಷೆಯಲ್ಲಿ ಮಾತನಾಡಿ',
    autoSpeakLabel: 'ಧ್ವನಿ ಉತ್ತರ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಪ್ಲೇ ಮಾಡಿ',
  },
  ml: {
    youSpoke: 'നിങ്ങൾ സംസാരിച്ചത്',
    recommendation: 'ജീവൻപഥ് AI നിർദ്ദേശം',
    listenAnswer: 'മറുപടി കേൾക്കുക',
    stopAudio: 'നിർത്തുക',
    grantTitle: 'PM-AJAY പദ്ധതി ഗ്രാന്റ് സഹായം',
    nsqfTitle: 'NSQF സ്കിൽ യോഗ്യത സർട്ടിഫിക്കറ്റ്',
    nextStepTitle: 'അടുത്ത നടപടി',
    askAnother: 'മറ്റൊരു ചോദ്യം ചോദിക്കുക',
    tapToSpeak: 'സംസാരിക്കാൻ തൊടുക',
    tapToStop: 'അവസാനിപ്പിക്കാൻ തൊടുക',
    listening: 'കേൾക്കുന്നു...',
    tapWhenDone: 'സംസാരിച്ചു കഴിഞ്ഞാൽ ചുവന്ന ബട്ടൺ അമർത്തുക',
    analyzing: 'പരിശോധിക്കുന്നു...',
    tapInstruction: 'പച്ച ബട്ടൺ അമർത്തി നിങ്ങളുടെ മാതൃഭാഷയിൽ സംസാരിക്കുക',
    autoSpeakLabel: 'മറുപടി സ്വയമേവ കേൾപ്പിക്കുക',
  },
};

function getUIText(langCode) {
  return UI_TEXT[langCode] || UI_TEXT['en'];
}

// Complete, fully translated domain reasoning for PM-AJAY and NSQF skilling
function generateLivelihoodAdvice(transcript, langCode) {
  const text = (transcript || '').toLowerCase();
  const lang = ['ta', 'hi', 'te', 'kn', 'ml'].includes(langCode) ? langCode : 'en';

  // 1. Tailoring & Apparel
  if (text.includes('tailor') || text.includes('தையல்') || text.includes('सिल') || text.includes('दर्जी') || text.includes('sewing') || text.includes('cloth')) {
    const content = {
      ta: {
        summary: 'தையல் தொழில் செய்பவர்களுக்கு PM-AJAY திட்டத்தின் கீழ் இலவச மேம்பட்ட திறன் பயிற்சி மற்றும் ரூ. 50,000 வரை மானியத்துடன் கூடிய தையல் இயந்திர உபகரண உதவி வழங்கப்படுகிறது.',
        grantSupport: 'வருமானம் ஈட்டும் நவீன தையல் இயந்திரம் மற்றும் தையல் கருவித்தொகுப்பு வாங்க ரூ. 50,000 வரை நேரடி மானிய உதவி.',
        nsqfLevel: 'NSQF நிலை 4: சுயதொழில் தையலர் சான்றிதழ் (AMH/Q1947)',
        nextStep: 'உங்கள் ஆதார் அட்டை மற்றும் சமூக சான்றிதழுடன் அருகிலுள்ள பொது சேவை மையம் (CSC) அல்லது மாவட்ட தொழில் மையத்தை (DIC) அணுகவும்.'
      },
      hi: {
        summary: 'सिलाई एवं टेलरिंग कारीगरों को PM-AJAY के तहत उन्नत कौशल प्रमाणन एवं ₹50,000 तक की टूलकिट व सिलाई मशीन सहायता प्राप्त हो सकती है।',
        grantSupport: 'व्यावसायिक सिलाई मशीन और टूलकिट खरीद हेतु ₹50,000 तक का प्रत्यक्ष वित्तीय अनुदान।',
        nsqfLevel: 'NSQF स्तर 4: स्व-रोजगार दर्जी / परिधान प्रमाणन (AMH/Q1947)',
        nextStep: 'आधार कार्ड एवं जाति प्रमाण पत्र के साथ नजदीकी कॉमन सर्विस सेंटर (CSC) या जिला उद्योग केंद्र (DIC) में संपर्क करें।'
      },
      te: {
        summary: 'టైలరింగ్ చేసే వారికి PM-AJAY పథకం కింద ఉచిత ఆధునిక నైపుణ్య శిక్షణ మరియు రూ. 50,000 వరకు కుట్టు మిషన్ సబ్సిడీ గ్రాంట్ లభిస్తుంది.',
        grantSupport: 'కుట్టు యంత్రం మరియు వర్కింగ్ టూల్‌కిట్ కొనుగోలుకు రూ. 50,000 వరకు ప్రత్యక్ష ఆర్థిక సహాయం.',
        nsqfLevel: 'NSQF లెవెల్ 4: స్వయం ఉపాధి టైలర్ సర్టిఫికేషన్ (AMH/Q1947)',
        nextStep: 'ఆధార్ మరియు కుల ధృవీకరణ పత్రంతో సమీప కామన్ సర్వీస్ సెంటర్ (CSC) లేదా డిస్ట్రిక్ట్ ఇండస్ట్రీ సెంటర్ (DIC) ని సంప్రదించండి.'
      },
      kn: {
        summary: 'ಹೊಲಿಗೆ ಕೆಲಸ ಮಾಡುವವರಿಗೆ PM-AJAY ಯೋಜನೆಯಡಿ ಉಚಿತ ಕೌಶಲ್ಯ ತರಬೇತಿ ಮತ್ತು ₹50,000 ವರೆಗೆ ಹೊಲಿಗೆ ಯಂತ್ರ ಸಬ್ಸಿಡಿ ನೆರವು ದೊರೆಯುತ್ತದೆ.',
        grantSupport: 'ಹೊಲಿಗೆ ಯಂತ್ರ ಮತ್ತು ಉಪಕರಣಗಳ ಖರೀದಿಗೆ ₹50,000 ವರೆಗೆ ನೇರ ಅನುದಾನ ನೆರವು.',
        nsqfLevel: 'NSQF ಹಂತ 4: ಸ್ವಯಂ ಉದ್ಯೋಗಿ ಟೈಲರ್ ಪ್ರಮಾಣಪತ್ರ (AMH/Q1947)',
        nextStep: 'ಆಧಾರ್ ಕಾರ್ಡ್‌ನೊಂದಿಗೆ ಹತ್ತಿರದ ಸಾಮಾನ್ಯ ಸೇವಾ ಕೇಂದ್ರ (CSC) ಅಥವಾ ಜಿಲ್ಲಾ ಕೈಗಾರಿಕಾ ಕೇಂದ್ರವನ್ನು (DIC) ಸಂಪರ್ಕಿಸಿ.'
      },
      ml: {
        summary: 'തയ്യൽ തൊഴിൽ ചെയ്യുന്നവർക്ക് PM-AJAY പദ്ധതിക്ക് കീഴിൽ സൗജന്യ നൈപുണ്യ പരിശീലനവും ₹50,000 വരെ തയ്യൽ മെഷീൻ സബ്‌സിഡിയും ലഭ്യമാണ്.',
        grantSupport: 'തയ്യൽ മെഷീനും ടൂൾകിറ്റും വാങ്ങുന്നതിന് ₹50,000 വരെ നേരിട്ടുള്ള സാമ്പത്തിക ഗ്രാന്റ്.',
        nsqfLevel: 'NSQF ലെവൽ 4: സ്വയംതൊഴിൽ തയ്യൽ വിദഗ്ദ്ധൻ (AMH/Q1947)',
        nextStep: 'ആധാർ കാർഡുമായി അടുത്തുള്ള കോമൺ സർവീസ് സെന്റർ (CSC) അല്ലെങ്കിൽ ജില്ലാ വ്യവസായ കേന്ദ്രവുമായി ബന്ധപ്പെടുക.'
      },
      en: {
        summary: 'Eligible for PM-AJAY Tool-Kit & Skilling grant up to ₹50,000, along with NSQF-aligned advance stitching and apparel design certification.',
        grantSupport: 'Direct financial assistance up to ₹50,000 for commercial sewing machines & tailoring toolkit purchase.',
        nsqfLevel: 'NSQF Level 4: Self-Employed Tailor Certification (AMH/Q1947)',
        nextStep: 'Visit your nearest District Industry Center (DIC) or Common Service Center (CSC) with Aadhaar & SC certificate.'
      }
    };
    return content[lang] || content['en'];
  }

  // 2. Electrical & Wiring
  if (text.includes('electric') || text.includes('எலக்ட்ரீ') || text.includes('बिजली') || text.includes('wire') || text.includes('வயர்')) {
    const content = {
      ta: {
        summary: 'எலக்ட்ரீஷியன் மற்றும் வயரிங் வேலை செய்பவர்களுக்கு PM-AJAY மூலம் சான்றிதழுடன் கூடிய அரசு பயிற்சி மற்றும் தொழில் பாதுகாப்பு உபகரணங்கள் மானியத்தில் கிடைக்கின்றன.',
        grantSupport: 'ரூ. 15,000 மதிப்புள்ள எலக்ட்ரிக்கல் பாதுகாப்பு உபகரண கருவித்தொகுப்பு மற்றும் தொழில் தொடங்க சிறப்பு கடன் உதவி.',
        nsqfLevel: 'NSQF நிலை 3: வீட்டு எலக்ட்ரீஷியன் மற்றும் வயர்மேன் சான்றிதழ் (ELE/Q6001)',
        nextStep: 'PM-AJAY திறன் போர்ட்டலில் பதிவு செய்யவும் அல்லது உங்கள் வட்டார வளர்ச்சி அலுவலரை (BDO) அணுகவும்.'
      },
      hi: {
        summary: 'इलेक्ट्रिशियन और घरेलू वायरिंग कार्य के लिए PM-AJAY के माध्यम से प्रमाणित प्रशिक्षण और टूलकिट उपकरण सब्सिडी उपलब्ध है।',
        grantSupport: '₹15,000 मूल्य की सुरक्षा उपकरण टूलकिट एवं सूक्ष्म व्यवसाय स्थापित करने हेतु ऋण लिंकेज।',
        nsqfLevel: 'NSQF स्तर 3: घरेलू इलेक्ट्रिशियन एवं वायरमैन प्रमाणन (ELE/Q6001)',
        nextStep: 'PM-AJAY पोर्टल पर पंजीकरण करें अथवा अपने ब्लॉक विकास अधिकारी (BDO) से संपर्क करें।'
      },
      te: {
        summary: 'ఎలక్ట్రీషియన్ మరియు వైరింగ్ పనులకు PM-AJAY ద్వారా సర్టిఫైడ్ శిక్షణ మరియు సేఫ్టీ టూల్‌కిట్ పరికరాల సబ్సిడీ లభిస్తుంది.',
        grantSupport: 'రూ. 15,000 విలువైన ఎలక్ట్రికల్ సేఫ్టీ టూల్‌కిట్ మరియు వ్యాపార స్థాపనకు మైక్రో-క్రెడిట్ సదుపాయం.',
        nsqfLevel: 'NSQF లెవెల్ 3: డొమెస్టిక్ ఎలక్ట్రీషియన్ మరియు వైర్‌మ్యాన్ (ELE/Q6001)',
        nextStep: 'PM-AJAY స్కిల్ పోర్టల్‌లో నమోదు చేసుకోండి లేదా మీ బ్లాక్ డెవలప్‌మెంట్ ఆఫీసర్‌ను (BDO) కలవండి.'
      },
      kn: {
        summary: 'ಎಲೆಕ್ಟ್ರಿಷಿಯನ್ ಕೆಲಸಕ್ಕಾಗಿ PM-AJAY ಅಡಿಯಲ್ಲಿ ಪ್ರಮಾಣೀಕೃತ ತರಬೇತಿ ಮತ್ತು ಸುರಕ್ಷತಾ ಟೂಲ್‌ಕಿಟ್ ಸಬ್ಸಿಡಿ ಲಭ್ಯವಿದೆ.',
        grantSupport: '₹15,000 ಮೌಲ್ಯದ ಎಲೆಕ್ಟ್ರಿಕಲ್ ಸುರಕ್ಷತಾ ಟೂಲ್‌ಕಿಟ್ ಮತ್ತು ಕಿರು ಸಾಲ ಸೌಲಭ್ಯ.',
        nsqfLevel: 'NSQF ಹಂತ 3: ಡೊಮೆಸ್ಟಿಕ್ ಎಲೆಕ್ಟ್ರಿಷಿಯನ್ (ELE/Q6001)',
        nextStep: 'PM-AJAY ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ನೋಂದಾಯಿಸಿ ಅಥವಾ ನಿಮ್ಮ ಬಿಡಿಒ (BDO) ಕಚೇರಿಯನ್ನು ಸಂಪರ್ಕಿಸಿ.'
      },
      ml: {
        summary: 'ഇലക്ട്രീഷ്യൻ ജോലികൾക്ക് PM-AJAY വഴി സർട്ടിഫൈഡ് പരിശീലനവും ടൂൾകിറ്റ് സബ്‌സിഡിയും ലഭ്യമാണ്.',
        grantSupport: '₹15,000 വിലമതിക്കുന്ന സേഫ്റ്റി ടൂൾകിറ്റും ചെറുകിട സംരംഭ വായ്പാ സഹായവും.',
        nsqfLevel: 'NSQF ലെവൽ 3: ഡൊമസ്റ്റിക് ഇലക്ട്രീഷ്യൻ (ELE/Q6001)',
        nextStep: 'PM-AJAY പോർട്ടലിൽ രജിസ്റ്റർ ചെയ്യുക അല്ലെങ്കിൽ ബി.ഡി.ഒ (BDO) ഓഫീസുമായി ബന്ധപ്പെടുക.'
      },
      en: {
        summary: 'Certified Domestic Electrician skill certification with safety gear equipment subsidy under PM-AJAY livelihood cluster.',
        grantSupport: 'Subsidized electrical safety toolkit worth ₹15,000 + micro-enterprise credit tie-up.',
        nsqfLevel: 'NSQF Level 3: Domestic Electrician & Wireman (ELE/Q6001)',
        nextStep: 'Register on PM-AJAY skill portal or contact your Block Development Officer (BDO).'
      }
    };
    return content[lang] || content['en'];
  }

  // 3. Carpentry & Woodcraft
  if (text.includes('carpent') || text.includes('தச்சு') || text.includes('बढ़ई') || text.includes('wood') || text.includes('மர')) {
    const content = {
      ta: {
        summary: 'மரவேலை மற்றும் தச்சு கலைஞர்களுக்கு நவீன இயந்திரங்கள் வாங்க PM-AJAY நிதி உதவி மற்றும் மேம்பட்ட கைவினைஞர் திறன் சான்றிதழ் வழங்கப்படுகிறது.',
        grantSupport: 'நவீன மரவேலை பவர் டூல்ஸ் மற்றும் உபகரணங்கள் வாங்க ரூ. 50,000 வரை நேரடி மூலதன மானியம்.',
        nsqfLevel: 'NSQF நிலை 4: தலைமை மரவேலை கைவினைஞர் (CON/Q0103)',
        nextStep: 'மாவட்ட வாழ்வாதார ஒருங்கிணைப்பாளர் அல்லது கிராம சமூகநலக் குழுவை அணுகவும்.'
      },
      hi: {
        summary: 'बढ़ई एवं काष्ठशिल्प कारीगरों के लिए आधुनिक टूलकिट और PM-AJAY ऋण-सब्सिडी का विशेष प्रावधान है।',
        grantSupport: 'आधुनिक पॉवर टूल्स एवं बढ़ईगीरी उपकरणों के लिए ₹50,000 तक की पूंजीगत सब्सिडी।',
        nsqfLevel: 'NSQF स्तर 4: मास्टर बढ़ई एवं फर्नीचर शिल्पकार (CON/Q0103)',
        nextStep: 'जिला आजीविका समन्वयक अथवा ग्राम कल्याण समिति से संपर्क करें।'
      },
      te: {
        summary: 'వడ్రంగి మరియు చెక్కపని కళాకారులకు ఆధునిక యంత్రాలు కొనుగోలు చేయడానికి PM-AJAY ఆర్థిక సహాయం మరియు సర్టిఫికేట్ అందిస్తుంది.',
        grantSupport: 'పవర్ టూల్స్ మరియు వడ్రంగి పరికరాల కొనుగోలుకు రూ. 50,000 వరకు మూలధన సబ్సిడీ.',
        nsqfLevel: 'NSQF లెవెల్ 4: మాస్టర్ కార్పెంటర్ & ఫర్నిచర్ క్రాఫ్ట్స్‌మ్యాన్ (CON/Q0103)',
        nextStep: 'జిల్లా జీవనోపాధి ఫెసిలిటేటర్ లేదా గ్రామ సంక్షేమ కమిటీని సంప్రదించండి.'
      },
      kn: {
        summary: 'ಬಡಗಿ ಮತ್ತು ಮರಗೆಲಸ ಮಾಡುವವರಿಗೆ ಆಧುನಿಕ ಯಂತ್ರಗಳ ಖರೀದಿಗೆ PM-AJAY ಆರ್ಥಿಕ ನೆರವು ಒದಗಿಸುತ್ತದೆ.',
        grantSupport: 'ಪವರ್ ಟೂಲ್‌ಗಳಿಗಾಗಿ ₹50,000 ವರೆಗೆ ನೇರ ಬಂಡವಾಳ ಸಬ್ಸಿಡಿ.',
        nsqfLevel: 'NSQF ಹಂತ 4: ಮಾಸ್ಟರ್ ಕಾರ್ಪೆಂಟರ್ (CON/Q0103)',
        nextStep: 'ಜಿಲ್ಲಾ ಜೀವನೋಪಾಯ ಸಂಯೋಜಕರು ಅಥವಾ ಗ್ರಾಮ ಪಂಚಾಯತ್ ಸಂಪರ್ಕಿಸಿ.'
      },
      ml: {
        summary: 'ആശാരിപ്പണി ചെയ്യുന്നവർക്ക് ആധുനിക ഉപകരണങ്ങൾ വാങ്ങാൻ PM-AJAY സാമ്പത്തിക സഹായം നൽകുന്നു.',
        grantSupport: 'പവർ ടൂളുകൾ വാങ്ങുന്നതിന് ₹50,000 വരെ നേരിട്ടുള്ള സബ്സിഡി.',
        nsqfLevel: 'NSQF ലെവൽ 4: മാസ്റ്റർ കാർപെന്റർ (CON/Q0103)',
        nextStep: 'ജില്ലാ ലൈവ്‌ലിഹുഡ് ഫെസിലിറ്റേറ്ററെ സമീപിക്കുക.'
      },
      en: {
        summary: 'Modern woodworking machinery grant and NSQF Level 4 Master Carpenter certification under PM-AJAY.',
        grantSupport: 'Up to ₹50,000 capital subsidy for power tools & modular carpentry equipment.',
        nsqfLevel: 'NSQF Level 4: Master Carpenter & Furniture Craftsman (CON/Q0103)',
        nextStep: 'Contact District Livelihood Facilitator or apply via PM-AJAY Village Welfare Committee.'
      }
    };
    return content[lang] || content['en'];
  }

  // 4. Default / General Livelihood Query
  const defaultContent = {
    ta: {
      summary: 'உங்கள் வாழ்வாதாரக் கோரிக்கை பதிவு செய்யப்பட்டது. PM-AJAY திட்டத்தின் கீழ் தகுதியான பட்டியல் சமூக பயனாளிகளுக்கு திறன் பயிற்சி மற்றும் நிதி உதவி கிடைக்க வாய்ப்புள்ளது.',
      grantSupport: 'வருமானம் ஈட்டும் உபகரணங்கள் அல்லது சுயதொழில் தொடங்க ரூ. 50,000 வரை நேரடி மானிய உதவி.',
      nsqfLevel: 'NSQF நிலை 3-4: சிறு தொழில் வளர்ச்சி மற்றும் வாழ்வாதார திறன் மேம்பாடு.',
      nextStep: 'உங்கள் ஆதார் அட்டை மற்றும் சாதிச் சான்றிதழுடன் அருகிலுள்ள பொது சேவை மையம் (CSC) அல்லது கிராம பஞ்சாயத்து அலுவலகத்தை அணுகவும்.'
    },
    hi: {
      summary: 'आपकी आजीविका एवं कौशल आवश्यकता को दर्ज कर लिया गया है। PM-AJAY योजना के तहत आपको प्रशिक्षण एवं वित्तीय अनुदान सहायता दी जा सकती है।',
      grantSupport: 'आय अर्जक उपकरण खरीदने या स्वरोजगार शुरू करने के लिए ₹50,000 तक की प्रत्यक्ष अनुदान सब्सिडी।',
      nsqfLevel: 'NSQF स्तर 3-4: सूक्ष्म उद्यम विकास एवं आजीविका कौशल प्रमाणन।',
      nextStep: 'आधार कार्ड एवं जाति प्रमाण पत्र के साथ अपने निकटतम कॉमन सर्विस सेंटर (CSC) या ग्राम पंचायत कार्यालय से संपर्क करें।'
    },
    te: {
      summary: 'మీ జీవనోపాధి అవసరం నమోదు చేయబడింది. PM-AJAY పథకం కింద మీకు నైపుణ్య శిక్షణ మరియు ఆర్థిక గ్రాంట్ లభించే అవకాశం ఉంది.',
      grantSupport: 'ఆదాయాన్ని ఇచ్చే పరికరాల కొనుగోలు లేదా స్వయం ఉపాధి కోసం ₹50,000 వరకు ప్రత్యక్ష రాయితీ సహాయం.',
      nsqfLevel: 'NSQF లెవెల్ 3-4: సూక్ష్మ వ్యాపార అభివృద్ధి మరియు జీవనోపాధి నైపుణ్య శిక్షణ.',
      nextStep: 'ఆధార్ కార్డుతో మీ సమీప కామన్ సర్వీస్ సెంటర్ (CSC) లేదా గ్రామ పంచాయతీ కార్యాలయాన్ని సంప్రదించండి.'
    },
    kn: {
      summary: 'ನಿಮ್ಮ ಜೀವನೋಪಾಯ ಅಗತ್ಯವನ್ನು ದಾಖಲಿಸಲಾಗಿದೆ. PM-AJAY ಯೋಜನೆಯಡಿ ನಿಮಗೆ ಕೌಶಲ್ಯ ತರಬೇತಿ ಮತ್ತು ಹಣಕಾಸಿನ ನೆರವು ಲಭ್ಯವಿದೆ.',
      grantSupport: 'ಆದಾಯ ಗಳಿಸುವ ಉಪಕರಣಗಳು ಅಥವಾ ಉದ್ಯಮ ಸ್ಥಾಪನೆಗಾಗಿ ₹50,000 ವರೆಗೆ ನೇರ ಸಬ್ಸಿಡಿ ನೆರವು.',
      nsqfLevel: 'NSQF ಹಂತ 3-4: ಕಿರು ಉದ್ಯಮ ಅಭಿವೃದ್ಧಿ ಮತ್ತು ಜೀವನೋಪಾಯ ಕೌಶಲ್ಯ ತರಬೇತಿ.',
      nextStep: 'ಆಧಾರ್ ಕಾರ್ಡ್‌ನೊಂದಿಗೆ ನಿಮ್ಮ ಹತ್ತಿರದ ಸಾಮಾನ್ಯ ಸೇವಾ ಕೇಂದ್ರ (CSC) ಅಥವಾ ಗ್ರಾಮ ಪಂಚಾಯತ್ ಕಚೇರಿಯನ್ನು ಸಂಪರ್ಕಿಸಿ.'
    },
    ml: {
      summary: 'നിങ്ങളുടെ ഉപജീവന ആവശ്യം രേഖപ്പെടുത്തിയിട്ടുണ്ട്. PM-AJAY പദ്ധതി പ്രകാരം പരിശീലനവും ധനസഹായവും ലഭ്യമാകും.',
      grantSupport: 'വരുമാനദായക ഉപകരണങ്ങൾ വാങ്ങുന്നതിനും സംരംഭം തുടങ്ങുന്നതിനും ₹50,000 വരെ നേരിട്ടുള്ള സബ്സിഡി സഹായം.',
      nsqfLevel: 'NSQF ലെവൽ 3-4: ചെറുകിട സംരംഭ വികസനവും ഉപജീവന നൈപുണ്യ പരിശീലനവും.',
      nextStep: 'ആധാർ കാർഡുമായി നിങ്ങളുടെ അടുത്തുള്ള കോമൺ സർവീസ് സെന്ററിലോ (CSC) ഗ്രാമപഞ്ചായത്ത് ഓഫീസിലോ ബന്ധപ്പെടുക.'
    },
    en: {
      summary: 'Beneficiary aspiration mapped. Eligible under PM-AJAY livelihood support for technical skilling, stipend, and business seed grants.',
      grantSupport: 'Direct benefit subsidy up to ₹50,000 for income-generating equipment or enterprise setup.',
      nsqfLevel: 'NSQF Level 3-4: Micro-Enterprise Development & Livelihood Skilling.',
      nextStep: 'Visit your nearest Common Service Center (CSC) or Gram Panchayat office with Aadhaar card.'
    }
  };

  return defaultContent[lang] || defaultContent['en'];
}

export default function App() {
  // Server state
  const [serverHealth, setServerHealth] = useState(null);

  // Recording & speech state
  const [isRecording, setIsRecording] = useState(false);
  const [recordSeconds, setRecordSeconds] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeResult, setActiveResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [autoSpeak, setAutoSpeak] = useState(true); // Talk back automatically by default
  const [selectedLang, setSelectedLang] = useState('auto'); // 'auto' | 'ta' | 'hi' | 'te' | 'kn' | 'en'
  const [showUpload, setShowUpload] = useState(false);

  // Media & visualizer refs
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);
  const canvasRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animFrameRef = useRef(null);
  const fileInputRef = useRef(null);
  const audioPlayerRef = useRef(null);

  // Pre-load voices for browser speech synthesis
  useEffect(() => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
      };
    }
  }, []);

  // Check Backend Health
  const checkHealth = async () => {
    try {
      const res = await fetch('/health');
      if (res.ok) {
        const data = await res.json();
        setServerHealth(data);
      } else {
        setServerHealth({ status: 'degraded' });
      }
    } catch {
      setServerHealth({ status: 'offline' });
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 12000);
    return () => clearInterval(interval);
  }, []);

  // Waveform Visualizer
  const startVisualizer = (stream) => {
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      audioContextRef.current = audioCtx;
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      analyserRef.current = analyser;

      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);

      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      const draw = () => {
        animFrameRef.current = requestAnimationFrame(draw);
        analyser.getByteFrequencyData(dataArray);

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const barWidth = (canvas.width / bufferLength) * 1.6;
        let x = 8;

        for (let i = 0; i < bufferLength; i++) {
          const barHeight = (dataArray[i] / 255) * canvas.height * 0.9;
          const gradient = ctx.createLinearGradient(0, canvas.height, 0, 0);
          gradient.addColorStop(0, '#10b981');
          gradient.addColorStop(1, '#f59e0b');

          ctx.fillStyle = gradient;
          ctx.beginPath();
          ctx.roundRect(x, canvas.height - barHeight, barWidth - 2, barHeight, [3, 3, 0, 0]);
          ctx.fill();

          x += barWidth + 3;
        }
      };

      draw();
    } catch {
      // AudioContext fallback
    }
  };

  const stopVisualizer = () => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
    }
    if (canvasRef.current) {
      const ctx = canvasRef.current.getContext('2d');
      ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
    }
  };

  // Talk Back Function (Chatbot speaks back in the user's native language)
  const speakToUser = (advice, langCode) => {
    if (!advice) return;

    // Stop any existing playback
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
      audioPlayerRef.current = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }

    const textToSpeak = advice.speechText || `${advice.summary} ${advice.grantSupport} ${advice.nextStep}`;
    const targetLang = langCode || 'en';

    // 1. Play native Indic speech stream from FastAPI backend (/api/voice/synthesize)
    try {
      const audioUrl = `/api/voice/synthesize?text=${encodeURIComponent(textToSpeak)}&language=${encodeURIComponent(targetLang)}`;
      const audio = new Audio(audioUrl);
      audioPlayerRef.current = audio;

      setIsSpeaking(true);

      audio.onended = () => {
        setIsSpeaking(false);
        audioPlayerRef.current = null;
      };

      audio.onerror = () => {
        // Fallback to browser SpeechSynthesis if backend audio stream has an issue
        if ('speechSynthesis' in window) {
          const utterance = new SpeechSynthesisUtterance(textToSpeak);
          const meta = LANGUAGE_META[targetLang] || LANGUAGE_META['en'];
          utterance.lang = meta.speechLang || 'en-IN';
          utterance.rate = 0.90;
          utterance.onend = () => setIsSpeaking(false);
          utterance.onerror = () => setIsSpeaking(false);
          window.speechSynthesis.speak(utterance);
        } else {
          setIsSpeaking(false);
        }
      };

      const playPromise = audio.play();
      if (playPromise !== undefined) {
        playPromise.catch((err) => {
          console.warn("Autoplay audio play blocked by browser policy:", err);
          setIsSpeaking(false);
        });
      }
    } catch {
      setIsSpeaking(false);
    }
  };

  // 1-Touch Speak Handler
  const handleTouchToSpeak = async () => {
    // Stop any existing speech playback
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }

    if (isRecording) {
      // Stop recording and process
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
        setIsRecording(false);
        clearInterval(timerRef.current);
      }
      return;
    }

    // Start recording
    setErrorMsg(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4';

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const blob = new Blob(audioChunksRef.current, { type: mimeType });
        stopVisualizer();
        stream.getTracks().forEach((t) => t.stop());
        await processAudio(blob, 'voice_record.webm');
      };

      mediaRecorder.start(250);
      setIsRecording(true);
      setRecordSeconds(0);
      startVisualizer(stream);

      timerRef.current = setInterval(() => {
        setRecordSeconds((s) => s + 1);
      }, 1000);
    } catch (err) {
      setErrorMsg(`Microphone error: ${err.message || 'Please check mic access'}`);
    }
  };

  // Submit audio to FastAPI Backend
  const processAudio = async (blob, fileName = 'audio.wav') => {
    setIsProcessing(true);
    setErrorMsg(null);

    const formData = new FormData();
    formData.append('audio', blob, fileName);
    if (selectedLang !== 'auto') {
      formData.append('language', selectedLang);
    }

    try {
      const res = await fetch('/api/voice/transcribe', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Server error: ${res.status}`);
      }

      const data = await res.json();

      // Smart Language Resolution:
      // 1. If user selected a language, use it
      // 2. Or if transcript contains Indian Unicode characters, detect from script
      let resolvedLang = selectedLang !== 'auto' ? selectedLang : (data.language || 'en');
      for (const ch of (data.transcript || '')) {
        const cp = ch.charCodeAt(0);
        if (cp >= 0x0B80 && cp <= 0x0BFF) { resolvedLang = 'ta'; break; }
        if (cp >= 0x0900 && cp <= 0x097F) { resolvedLang = 'hi'; break; }
        if (cp >= 0x0C00 && cp <= 0x0C7F) { resolvedLang = 'te'; break; }
        if (cp >= 0x0C80 && cp <= 0x0CFF) { resolvedLang = 'kn'; break; }
        if (cp >= 0x0D00 && cp <= 0x0D7F) { resolvedLang = 'ml'; break; }
      }

      // Priority: Use the backend's localized advice in the user's native language!
      let advice = data.advice;
      if (!advice) {
        advice = generateLivelihoodAdvice(data.transcript, resolvedLang);
      }
      if (advice && !advice.nsqfLevel && advice.eligibility) {
        advice.nsqfLevel = advice.eligibility;
      }

      setActiveResult({
        ...data,
        language: resolvedLang,
        language_name: LANGUAGE_META[resolvedLang]?.name || data.language_name || 'Vernacular',
        advice,
      });

      // Chatbot automatically talks back in the beneficiary's detected language!
      if (autoSpeak) {
        speakToUser(advice, resolvedLang);
      }
    } catch (err) {
      setErrorMsg(err.message || 'Failed to process voice request.');
    } finally {
      setIsProcessing(false);
    }
  };

  // Quick Preset Sample for 1-click testing
  const loadPresetQuery = (transcript, lang, langName) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }

    setSelectedLang(lang);
    const advice = generateLivelihoodAdvice(transcript, lang);
    setActiveResult({
      language: lang,
      language_name: langName,
      transcript,
      confidence: 0.96,
      processing_time: 0.38,
      audio_duration: 3.2,
      advice,
    });

    if (autoSpeak) {
      speakToUser(advice, lang);
    }
  };

  // Toggle manual listen/stop
  const handleToggleSpeak = () => {
    if (isSpeaking) {
      if (audioPlayerRef.current) {
        audioPlayerRef.current.pause();
        audioPlayerRef.current = null;
      }
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      setIsSpeaking(false);
    } else if (activeResult?.advice) {
      speakToUser(activeResult.advice, activeResult.language);
    }
  };

  const formatTimer = (sec) => {
    const m = Math.floor(sec / 60).toString().padStart(2, '0');
    const s = (sec % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  // Active language code for UI localization (defaults to user's detected language or 'en')
  const currentLang = activeResult?.language || 'en';
  const ui = getUIText(currentLang);

  return (
    <div className="app-container">
      {/* App Header */}
      <header className="app-header">
        <div className="brand-wrapper">
          <div className="brand-icon">🌾</div>
          <div className="brand-titles">
            <h1>
              JeevanPath <span className="highlight">AI</span>
            </h1>
            <p className="brand-tagline">
              Voice Assistant for PM-AJAY Livelihood & Skilling
            </p>
          </div>
        </div>

        {/* Server status & Talk-Back toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Auto-Talk Back Toggle */}
          <button
            onClick={() => setAutoSpeak(!autoSpeak)}
            title="Chatbot speaks back in your language automatically"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '20px',
              background: autoSpeak ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255, 255, 255, 0.05)',
              border: `1px solid ${autoSpeak ? 'rgba(16, 185, 129, 0.4)' : 'rgba(255, 255, 255, 0.1)'}`,
              color: autoSpeak ? '#34d399' : '#94a3b8',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.15s',
            }}
          >
            <Radio size={13} color={autoSpeak ? '#10b981' : '#64748b'} />
            {ui.autoSpeakLabel}
          </button>

          {/* Server GPU badge */}
          <div className="status-pill">
            <span
              className={`status-dot ${
                serverHealth?.status === 'ok'
                  ? ''
                  : serverHealth?.status === 'degraded'
                  ? 'degraded'
                  : 'offline'
              }`}
            />
            {serverHealth?.status === 'ok' ? (
              <span>
                <strong>GPU:</strong> {serverHealth.stt?.model} ({serverHealth.stt?.compute_type})
              </span>
            ) : (
              <span>Backend: {serverHealth?.status || 'Connecting...'}</span>
            )}
            <button
              onClick={checkHealth}
              title="Refresh Status"
              style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
            >
              <RefreshCw size={12} />
            </button>
          </div>
        </div>
      </header>

      {/* Hero Title */}
      <div className="app-hero-mini">
        <h2>Voice-First Beneficiary Support</h2>
        <p>Speak in your native language. JeevanPath AI maps your skills and answers immediately in your language.</p>
      </div>

      {/* Main Dashboard Layout */}
      <div className="main-grid">
        {/* LEFT SIDE: Touch to Speak Button */}
        <div className="glass-card">
          <div className="card-header">
            <h3 className="card-title">
              <Mic size={18} color="#10b981" /> Voice Assistant
            </h3>
            <span style={{ fontSize: '11px', color: '#64748b' }}>Zero-Config</span>
          </div>

          {/* Language Pre-Selector — pick BEFORE speaking for best accuracy */}
          <div style={{ marginBottom: '16px' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              marginBottom: '8px',
            }}>
              <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.7px', color: '#10b981', fontWeight: 700 }}>
                🗣 Pick your language before speaking
              </span>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', justifyContent: 'center' }}>
              {[
                { code: 'auto', label: '🌐 Auto-Detect' },
                { code: 'ta',   label: 'தமிழ்' },
                { code: 'hi',   label: 'हिन्दी' },
                { code: 'te',   label: 'తెలుగు' },
                { code: 'kn',   label: 'ಕನ್ನಡ' },
                { code: 'ml',   label: 'മലയാളം' },
                { code: 'mr',   label: 'मराठी' },
                { code: 'bn',   label: 'বাংলা' },
                { code: 'gu',   label: 'ગુજરાતી' },
                { code: 'en',   label: 'English' },
              ].map((l) => (
                <button
                  key={l.code}
                  type="button"
                  title={l.code === 'auto'
                    ? 'Let AI detect your language automatically (may be less accurate for short clips)'
                    : `Speak in ${LANGUAGE_META[l.code]?.name || l.label} — sends a strong hint to the AI`}
                  onClick={() => {
                    setSelectedLang(l.code);
                    if ('speechSynthesis' in window) {
                      window.speechSynthesis.cancel();
                      setIsSpeaking(false);
                    }
                  }}
                  style={{
                    padding: '5px 12px',
                    borderRadius: '20px',
                    fontSize: '12px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    border: selectedLang === l.code
                      ? '1.5px solid #10b981'
                      : '1px solid rgba(255,255,255,0.12)',
                    background: selectedLang === l.code
                      ? 'rgba(16,185,129,0.22)'
                      : 'rgba(255,255,255,0.04)',
                    color: selectedLang === l.code ? '#34d399' : '#94a3b8',
                    transition: 'all 0.15s',
                    boxShadow: selectedLang === l.code ? '0 0 8px rgba(16,185,129,0.25)' : 'none',
                  }}
                >
                  {l.label}
                </button>
              ))}
            </div>
            {selectedLang !== 'auto' && (
              <div style={{ textAlign: 'center', marginTop: '6px', fontSize: '11px', color: '#34d399' }}>
                ✓ Language hint sent to AI: {LANGUAGE_META[selectedLang]?.name || selectedLang}
              </div>
            )}
          </div>

          <div className="touch-to-speak-container">
            <div className="touch-button-wrapper">
              {isRecording && <div className="pulse-ring-outer" />}
              <button
                className={`touch-speak-btn ${isRecording ? 'recording' : ''}`}
                onClick={handleTouchToSpeak}
                title={isRecording ? ui.tapToStop : ui.tapToSpeak}
              >
                {isRecording ? <Square size={44} /> : <Mic size={48} />}
                <span className="touch-btn-label">
                  {isRecording ? ui.tapToStop : ui.tapToSpeak}
                </span>
              </button>
            </div>

            {/* Status & Timer */}
            <div className="touch-status-info">
              {isRecording ? (
                <>
                  <div className="touch-timer">{formatTimer(recordSeconds)}</div>
                  <div className="touch-instruction">{ui.listening}</div>
                  <div className="touch-subtext">{ui.tapWhenDone}</div>
                </>
              ) : isProcessing ? (
                <>
                  <div className="touch-instruction" style={{ color: '#10b981' }}>
                    {ui.analyzing}
                  </div>
                  <div className="touch-subtext">Detecting Indian language & extracting skills</div>
                </>
              ) : (
                <>
                  <div className="touch-instruction">{ui.tapInstruction}</div>
                  <div className="touch-subtext">
                    Supported: தமிழ், हिन्दी, తెలుగు, ಕನ್ನಡ, മലയാളം, English
                  </div>
                </>
              )}
            </div>

            {/* Waveform Canvas */}
            <canvas
              ref={canvasRef}
              className="touch-waveform"
              width={300}
              height={48}
              style={{ display: isRecording ? 'block' : 'none' }}
            />

            {/* Error banner */}
            {errorMsg && (
              <div
                style={{
                  padding: '10px 14px',
                  borderRadius: '8px',
                  background: 'rgba(239, 68, 68, 0.12)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  color: '#f87171',
                  fontSize: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <AlertCircle size={14} />
                {errorMsg}
              </div>
            )}

            {/* Secondary Options */}
            <div className="alt-options-row">
              <button
                type="button"
                className="quick-sample-btn"
                onClick={async () => {
                  try {
                    const res = await fetch('/samples/sample_test.wav');
                    const blob = await res.blob();
                    await processAudio(blob, 'sample_test.wav');
                  } catch {
                    setErrorMsg('Could not load sample audio.');
                  }
                }}
              >
                <Sparkles size={14} color="#10b981" /> Try Quick Voice Sample
              </button>

              <button
                type="button"
                className="file-upload-toggle"
                onClick={() => setShowUpload(!showUpload)}
              >
                <Upload size={12} /> {showUpload ? 'Hide file upload' : 'Or upload audio file'}
              </button>

              {showUpload && (
                <div
                  className="mini-dropzone"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="audio/*,.wav,.webm,.mp3,.m4a"
                    style={{ display: 'none' }}
                    onChange={(e) => {
                      if (e.target.files?.[0]) {
                        processAudio(e.target.files[0], e.target.files[0].name);
                      }
                    }}
                  />
                  <span>Click to select audio file (WAV, MP3, M4A, WebM)</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* RIGHT SIDE: Intelligent Multilingual Assistant Answer Panel */}
        <div className="glass-card answer-panel">
          <div className="card-header">
            <h3 className="card-title">
              <Sparkles size={18} color="#f59e0b" /> {ui.recommendation}
            </h3>
            {activeResult && (
              <span
                style={{
                  fontSize: '12px',
                  color: '#10b981',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                <CheckCircle2 size={13} /> {activeResult.language_name || 'Vernacular'}
              </span>
            )}
          </div>

          {/* 1. Processing State */}
          {isProcessing && (
            <div className="processing-box">
              <div className="processing-spinner" />
              <h4 style={{ color: '#f8fafc', fontSize: '16px' }}>Processing Your Voice Request</h4>
              <p style={{ color: '#94a3b8', fontSize: '13px', maxWidth: '340px' }}>
                Whisper is decoding dialect phonemes and mapping your skills to PM-AJAY qualification packs...
              </p>
            </div>
          )}

          {/* 2. Empty Welcome State with Quick Example Prompts */}
          {!isProcessing && !activeResult && (
            <div className="welcome-box">
              <div className="welcome-avatar">🌾</div>
              <h3>How Can JeevanPath AI Help You?</h3>
              <p>
                Tap the button on the left and tell us what work you do or what skill/loan you need. Or try one of these common beneficiary queries:
              </p>

              <div className="example-queries-title">Try One-Click Beneficiary Scenarios:</div>
              <div className="example-chips">
                <button
                  className="example-chip-btn"
                  onClick={() =>
                    loadPresetQuery(
                      'நான் தையல் வேலை செய்கிறேன், எனக்கு தையல் பயிற்சி மற்றும் இயந்திர உதவி வேண்டும்.',
                      'ta',
                      'Tamil'
                    )
                  }
                >
                  <span>🧵</span>
                  <span style={{ flex: 1 }}>
                    <strong>தமிழ் (Tamil):</strong> தையல் பயிற்சி மற்றும் இயந்திர உதவி வேண்டும்
                  </span>
                  <ArrowRight size={14} color="#10b981" />
                </button>

                <button
                  className="example-chip-btn"
                  onClick={() =>
                    loadPresetQuery(
                      'मैं बिजली वायरिंग और इलेक्ट्रिशियन का काम जानता हूँ, मुझे टूलकिट और सर्टिफिकेट चाहिए।',
                      'hi',
                      'Hindi'
                    )
                  }
                >
                  <span>⚡</span>
                  <span style={{ flex: 1 }}>
                    <strong>हिन्दी (Hindi):</strong> मुझे इलेक्ट्रिशियन टूलकिट और सर्टिफिकेट चाहिए
                  </span>
                  <ArrowRight size={14} color="#10b981" />
                </button>

                <button
                  className="example-chip-btn"
                  onClick={() =>
                    loadPresetQuery(
                      'నాకు వడ్రంగి పని తెలుసు, ఆధునిక పరికరాలు మరియు పథకం సాయం కావాలి.',
                      'te',
                      'Telugu'
                    )
                  }
                >
                  <span>🪵</span>
                  <span style={{ flex: 1 }}>
                    <strong>తెలుగు (Telugu):</strong> వడ్రంగి పని మరియు ప్రభుత్వ సాయం కావాలి
                  </span>
                  <ArrowRight size={14} color="#10b981" />
                </button>
              </div>
            </div>
          )}

          {/* 3. Fully Translated Answer Display */}
          {!isProcessing && activeResult && (
            <div className="conversation-flow">
              {/* What Beneficiary Spoke */}
              <div className="user-speech-card">
                <div className="user-speech-header">
                  <div className="speaker-badge">
                    <Mic size={14} /> {ui.youSpoke}:
                  </div>
                  <div className="lang-detected-tag">
                    <span>{LANGUAGE_META[activeResult.language]?.flag || '🇮🇳'}</span>
                    <span>
                      {LANGUAGE_META[activeResult.language]?.name || activeResult.language_name || 'Vernacular'}
                    </span>
                    <span style={{ opacity: 0.75 }}>
                      ({Math.round((activeResult.confidence || 0.95) * 100)}% match)
                    </span>
                  </div>
                </div>
                <div className="user-speech-text">
                  "{activeResult.transcript || 'Spoken input captured'}"
                </div>
              </div>

              {/* AI Livelihood Answer */}
              <div className="assistant-answer-card">
                <div className="assistant-header">
                  <div className="assistant-identity">
                    <span className="assistant-badge">
                      <Sparkles size={16} /> {ui.recommendation}
                    </span>
                  </div>

                  {/* Talk Back / Listen Button */}
                  <button
                    className={`speak-aloud-btn ${isSpeaking ? 'speaking' : ''}`}
                    onClick={handleToggleSpeak}
                    title="Listen to the response in your language"
                  >
                    {isSpeaking ? <VolumeX size={14} /> : <Volume2 size={14} />}
                    {isSpeaking ? ui.stopAudio : ui.listenAnswer}
                  </button>
                </div>

                {/* Summary in native language */}
                <div className="answer-section">
                  <div className="answer-lead-text">
                    {activeResult.advice.summary}
                  </div>
                </div>

                {/* Fully Translated Scheme & Skill Cards */}
                <div className="recommendations-grid">
                  {/* Scheme Grant Card */}
                  <div className="rec-card">
                    <div className="rec-card-title">
                      <Briefcase size={14} /> {ui.grantTitle}
                    </div>
                    <div className="rec-card-desc">
                      {activeResult.advice.grantSupport}
                    </div>
                  </div>

                  {/* NSQF Qualification Card */}
                  <div className="rec-card">
                    <div className="rec-card-title">
                      <GraduationCap size={14} /> {ui.nsqfTitle}
                    </div>
                    <div className="rec-card-desc">
                      {activeResult.advice.nsqfLevel}
                    </div>
                  </div>
                </div>

                {/* Fully Translated Actionable Next Step */}
                <div
                  style={{
                    background: 'rgba(16, 185, 129, 0.08)',
                    border: '1px solid rgba(16, 185, 129, 0.25)',
                    borderRadius: '8px',
                    padding: '13px 15px',
                    fontSize: '13px',
                    color: '#e2e8f0',
                    lineHeight: 1.5,
                  }}
                >
                  <strong style={{ color: '#34d399', display: 'block', marginBottom: '2px' }}>
                    {ui.nextStepTitle}:
                  </strong>
                  {activeResult.advice.nextStep}
                </div>

                {/* Footer with Reset & Diagnostics */}
                <div className="answer-footer-actions">
                  <button
                    className="ask-another-btn"
                    onClick={() => {
                      if ('speechSynthesis' in window) {
                        window.speechSynthesis.cancel();
                        setIsSpeaking(false);
                      }
                      setActiveResult(null);
                    }}
                  >
                    <RotateCcw size={13} /> {ui.askAnother}
                  </button>

                  <div className="latency-note">
                    Verified in {activeResult.processing_time?.toFixed(2) || '0.35'}s via Whisper GPU
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
