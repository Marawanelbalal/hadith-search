export const POPULAR_QUERIES_EN = [
  'Prayer times',
  'Fasting',
  'Charity',
  'Patience',
  'Forgiveness',
  'Knowledge',
  'Mercy',
  'Truthfulness',
];

export const POPULAR_QUERIES_AR = [
  'أوقات الصلاة',
  'الصيام',
  'الصدقة',
  'الصبر',
  'المغفرة',
  'العلم',
  'الرحمة',
  'الصدق',
];

export const GRADE_COLORS: Record<string, { bg: string; text: string; hex: string }> = {
  'Sahih':              { bg: 'bg-grade-sahih',      text: 'text-white', hex: '#16a34a' },
  'Hasan':              { bg: 'bg-grade-hasan',      text: 'text-white', hex: '#2563eb' },
  "Da'if (Weak)":       { bg: 'bg-grade-daif',       text: 'text-white', hex: '#d97706' },
  'Maudu (Fabricated)': { bg: 'bg-grade-fabricated', text: 'text-white', hex: '#dc2626' },
  'Unknown':            { bg: 'bg-grade-unknown',    text: 'text-white', hex: '#6b7280' },
};

export const BOOK_DISPLAY_NAMES: Record<string, { en: string; ar: string }> = {
  'Sahih al-Bukhari': { en: 'Sahih al-Bukhari', ar: 'صحيح البخاري' },
  'Sahih Muslim':     { en: 'Sahih Muslim',     ar: 'صحيح مسلم' },
  "Jami` at-Tirmidhi": { en: "Jami' at-Tirmidhi", ar: 'جامع الترمذي' },
  'Sunan Abi Dawud':  { en: 'Sunan Abi Dawud',  ar: 'سنن أبي داود' },
  'Sunan Ibn Majah':   { en: 'Sunan Ibn Majah',   ar: 'سنن ابن ماجه' },
  "Sunan an-Nasa'i":  { en: "Sunan an-Nasa'i",  ar: 'سنن النسائي' },
};
