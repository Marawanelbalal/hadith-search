import type { Hadith, Book, AlgorithmResult, BenchmarkEntry, NavItem } from '../types';

// ─── Navigation ───────────────────────────────────────────────
export const navItems: NavItem[] = [
  { label: 'Search', path: '/results', icon: 'search' },
  { label: 'Benchmarks', path: '/benchmarks', icon: 'analytics' },
  { label: 'Algorithm Comparison', path: '/dev', icon: 'code' },
];

// ─── Books ────────────────────────────────────────────────────
export const books: Book[] = [
  {
    id: 'bukhari',
    name: 'Sahih al-Bukhari',
    arabicName: 'صحيح البخاري',
    hadithCount: 7563,
    description: 'The most authentic collection of hadith, compiled by Imam Muhammad al-Bukhari.',
  },
  {
    id: 'muslim',
    name: 'Sahih Muslim',
    arabicName: 'صحيح مسلم',
    hadithCount: 5362,
    description: 'The second most authentic hadith collection, compiled by Imam Muslim ibn al-Hajjaj.',
  },
  {
    id: 'tirmidhi',
    name: 'Jami al-Tirmidhi',
    arabicName: 'جامع الترمذي',
    hadithCount: 3956,
    description: 'One of the six canonical hadith collections, compiled by Imam al-Tirmidhi.',
  },
  {
    id: 'abudawud',
    name: 'Sunan Abu Dawud',
    arabicName: 'سنن أبي داود',
    hadithCount: 5274,
    description: 'A major hadith collection focusing on legal rulings, by Imam Abu Dawud.',
  },
  {
    id: 'nasai',
    name: 'Sunan al-Nasai',
    arabicName: 'سنن النسائي',
    hadithCount: 5758,
    description: 'One of the six canonical collections, known for its focus on legal traditions.',
  },
  {
    id: 'ibnmajah',
    name: 'Sunan Ibn Majah',
    arabicName: 'سنن ابن ماجه',
    hadithCount: 4341,
    description: 'The sixth of the six canonical hadith collections, by Imam Ibn Majah.',
  },
];

// ─── Hadith Collection ────────────────────────────────────────
export const hadithCollection: Hadith[] = [
  {
    id: 'h1',
    book: 'Sahih al-Bukhari',
    bookNumber: 9,
    hadithNumber: 5,
    grade: 'sahih',
    arabicText: 'حَدَّثَنَا عَبْدُ اللَّهِ بْنُ يُوسُفَ، قَالَ أَخْبَرَنَا مَالِكٌ، عَنْ أَبِي الزِّنَادِ، عَنِ الأَعْرَجِ، عَنْ أَبِي هُرَيْرَةَ، أَنَّ رَسُولَ اللَّهِ صلى الله عليه وسلم قَالَ ‏"‏ يَتَعَاقَبُونَ فِيكُمْ مَلاَئِكَةٌ بِاللَّيْلِ وَمَلاَئِكَةٌ بِالنَّهَارِ، وَيَجْتَمِعُونَ فِي صَلاَةِ الْفَجْرِ وَصَلاَةِ الْعَصْرِ... ‏"‏',
    englishText: 'Narrated Abu Huraira: Allah\'s Messenger (ﷺ) said, "Angels come to you in succession by night and day and all of them get together at the time of the Fajr and \'Asr prayers. Those who have passed the night with you ascend, and Allah asks them — though He knows everything about you — "In what state did you leave my slaves?" They reply, "When we left them, they were praying, and when we came to them, they were praying."',
    narrator: 'Abu Huraira',
    topic: 'Prayer',
  },
  {
    id: 'h2',
    book: 'Sahih Muslim',
    bookNumber: 1,
    hadithNumber: 38,
    grade: 'sahih',
    arabicText: 'عَنْ أَبِي هُرَيْرَةَ، قَالَ: قَالَ رَسُولُ اللَّهِ صلى الله عليه وسلم: ‏"‏مَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ الآخِرِ فَلْيَقُلْ خَيْرًا أَوْ لِيَصْمُتْ، وَمَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ الآخِرِ فَلْيُكْرِمْ جَارَهُ، وَمَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ الآخِرِ فَلْيُكْرِمْ ضَيْفَهُ‏"‏',
    englishText: 'Narrated Abu Huraira: The Messenger of Allah (ﷺ) said, "Whoever believes in Allah and the Last Day should speak good or remain silent; whoever believes in Allah and the Last Day should honor his neighbor; and whoever believes in Allah and the Last Day should honor his guest."',
    narrator: 'Abu Huraira',
    topic: 'Manners',
  },
  {
    id: 'h3',
    book: 'Jami al-Tirmidhi',
    bookNumber: 2,
    hadithNumber: 108,
    grade: 'hasan-sahih',
    arabicText: 'حَدَّثَنَا قُتَيْبَةُ، حَدَّثَنَا اللَّيْثُ، عَنِ ابْنِ عَجْلاَنَ، عَنِ الْقَعْقَاعِ، عَنْ أَبِي صَالِحٍ، عَنْ أَبِي هُرَيْرَةَ، أَنَّ رَسُولَ اللَّهِ صلى الله عليه وسلم قَالَ: ‏"‏الطُّهُورُ شَطْرُ الإِيمَانِ‏"‏',
    englishText: 'Narrated Abu Huraira: The Messenger of Allah (ﷺ) said, "Purity is half of faith (iman)."',
    narrator: 'Abu Huraira',
    topic: 'Purification',
  },
  {
    id: 'h4',
    book: 'Sunan Abu Dawud',
    bookNumber: 2,
    hadithNumber: 61,
    grade: 'hasan',
    arabicText: 'عَنْ عَبْدِ اللَّهِ بْنِ عَمْرٍو، عَنِ النَّبِيِّ صلى الله عليه وسلم قَالَ: ‏"‏الرَّاحِمُونَ يَرْحَمُهُمُ الرَّحْمَنُ، ارْحَمُوا أَهْلَ الأَرْضِ يَرْحَمْكُمْ أَهْلُ السَّمَاءِ‏"‏',
    englishText: 'Narrated Abdullah ibn Amr: The Prophet (ﷺ) said, "The Merciful shows mercy to those who are merciful. Show mercy to those who are on earth, and the One in heaven will show mercy to you."',
    narrator: 'Abdullah ibn Amr',
    topic: 'Mercy',
  },
  {
    id: 'h5',
    book: 'Sahih al-Bukhari',
    bookNumber: 4,
    hadithNumber: 162,
    grade: 'sahih',
    arabicText: 'حَدَّثَنَا أَبُو النُّعْمَانِ، حَدَّثَنَا حَمَّادُ بْنُ زَيْدٍ، عَنْ أَيُّوبَ، عَنْ أَبِي قِلاَبَةَ، عَنْ أَنَسٍ، عَنِ النَّبِيِّ صلى الله عليه وسلم قَالَ: ‏"‏لاَ يُؤْمِنُ أَحَدُكُمْ حَتَّى يُحِبَّ لأَخِيهِ مَا يُحِبُّ لِنَفْسِهِ‏"‏',
    englishText: 'Narrated Anas: The Prophet (ﷺ) said, "None of you truly believes until he loves for his brother what he loves for himself."',
    narrator: 'Anas ibn Malik',
    topic: 'Faith',
  },
  {
    id: 'h6',
    book: 'Sunan al-Nasai',
    bookNumber: 6,
    hadithNumber: 335,
    grade: 'daif-hasan',
    arabicText: 'عَنْ أَبِي هُرَيْرَةَ، قَالَ: قَالَ رَسُولُ اللَّهِ صلى الله عليه وسلم: ‏"‏تَسَحَّرُوا فَإِنَّ فِي السَّحُورِ بَرَكَةً‏"‏',
    englishText: 'Narrated Abu Huraira: The Messenger of Allah (ﷺ) said, "Eat suhoor (pre-dawn meal), for in suhoor there is blessing."',
    narrator: 'Abu Huraira',
    topic: 'Fasting',
  },
  {
    id: 'h7',
    book: 'Sunan Ibn Majah',
    bookNumber: 5,
    hadithNumber: 225,
    grade: 'daif',
    arabicText: 'عَنِ ابْنِ عَبَّاسٍ، قَالَ: قَالَ رَسُولُ اللَّهِ صلى الله عليه وسلم: ‏"‏مَنْ لَزِمَ الاِسْتِغْفَارَ جَعَلَ اللَّهُ لَهُ مِنْ كُلِّ ضِيقٍ مَخْرَجًا وَمِنْ كُلِّ هَمٍّ فَرَجًا وَرَزَقَهُ مِنْ حَيْثُ لاَ يَحْتَسِبُ‏"‏',
    englishText: 'Narrated Ibn Abbas: The Messenger of Allah (ﷺ) said, "Whoever constantly seeks forgiveness, Allah will appoint for him a way out of every distress, and a relief from every anxiety, and will provide for him from where he did not reckon."',
    narrator: 'Ibn Abbas',
    topic: 'Forgiveness',
  },
  {
    id: 'h8',
    book: 'Sahih Muslim',
    bookNumber: 4,
    hadithNumber: 2070,
    grade: 'sahih',
    arabicText: 'عَنْ أَبِي هُرَيْرَةَ، أَنَّ رَسُولَ اللَّهِ صلى الله عليه وسلم قَالَ: ‏"‏مَنْ سَلَكَ طَرِيقًا يَلْتَمِسُ فِيهِ عِلْمًا سَهَّلَ اللَّهُ لَهُ طَرِيقًا إِلَى الْجَنَّةِ‏"‏',
    englishText: 'Narrated Abu Huraira: The Messenger of Allah (ﷺ) said, "Whoever treads a path in search of knowledge, Allah will make easy for him a path to Paradise."',
    narrator: 'Abu Huraira',
    topic: 'Knowledge',
  },
  {
    id: 'h9',
    book: 'Jami al-Tirmidhi',
    bookNumber: 12,
    hadithNumber: 2483,
    grade: 'hasan',
    arabicText: 'عَنْ أَبِي الدَّرْدَاءِ، قَالَ: سَمِعْتُ رَسُولَ اللَّهِ صلى الله عليه وسلم يَقُولُ: ‏"‏إِنَّمَا الْعِلْمُ بِالتَّعَلُّمِ وَإِنَّمَا الْحِلْمُ بِالتَّحَلُّمِ‏"‏',
    englishText: 'Narrated Abu Darda: I heard the Messenger of Allah (ﷺ) say, "Knowledge is attained through learning, and forbearance through practicing forbearance."',
    narrator: 'Abu Darda',
    topic: 'Knowledge',
  },
  {
    id: 'h10',
    book: 'Sahih al-Bukhari',
    bookNumber: 3,
    hadithNumber: 27,
    grade: 'sahih',
    arabicText: 'حَدَّثَنَا سُلَيْمَانُ بْنُ حَرْبٍ، حَدَّثَنَا شُعْبَةُ، عَنْ قَتَادَةَ، عَنْ أَنَسٍ، عَنِ النَّبِيِّ صلى الله عليه وسلم قَالَ: ‏"‏لاَ صَلاَةَ لِمَنْ لَمْ يَقْرَأْ بِفَاتِحَةِ الْكِتَابِ‏"‏',
    englishText: 'Narrated Anas: The Prophet (ﷺ) said, "There is no prayer for the one who does not recite the Opening of the Book (Al-Fatihah)."',
    narrator: 'Anas ibn Malik',
    topic: 'Prayer',
  },
];

// ─── Hadith of the Day ────────────────────────────────────────
export const hadithOfTheDay: Hadith = {
  id: 'hotd',
  book: 'Sahih al-Bukhari',
  bookNumber: 2,
  hadithNumber: 12,
  grade: 'sahih',
  arabicText: 'عَنْ أَبِي هُرَيْرَةَ رَضِيَ اللَّهُ عَنْهُ، أَنَّ رَسُولَ اللَّهِ صلى الله عليه وسلم قَالَ: ‏"‏مَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ الآخِرِ فَلْيَقُلْ خَيْرًا أَوْ لِيَصْمُتْ، وَمَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ الآخِرِ فَلْيُكْرِمْ جَارَهُ، وَمَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ الآخِرِ فَلْيُكْرِمْ ضَيْفَهُ‏"‏',
  englishText: 'Narrated Abu Huraira: The Messenger of Allah (ﷺ) said, "Whoever believes in Allah and the Last Day should speak good or remain silent; whoever believes in Allah and the Last Day should honor his neighbor; and whoever believes in Allah and the Last Day should honor his guest."',
  narrator: 'Abu Huraira',
  topic: 'Manners',
};

// ─── Algorithm Results (Dev Mode) ─────────────────────────────
export const algorithmResults: AlgorithmResult[] = [
  {
    id: 'algo-a',
    algorithmName: 'BM25 + PRF',
    shortLabel: 'A',
    color: 'bg-primary',
    results: [
      hadithCollection[0], // Prayer - Abu Huraira
      hadithCollection[4], // Faith - Anas
      hadithCollection[9], // Prayer - Al-Fatihah
      hadithCollection[7], // Knowledge - Abu Huraira
    ],
  },
  {
    id: 'algo-b',
    algorithmName: 'Neural Bi-Encoder',
    shortLabel: 'B',
    color: 'bg-secondary-fixed-dim',
    results: [
      hadithCollection[2], // Purification
      hadithCollection[3], // Mercy
      hadithCollection[8], // Knowledge - Abu Darda
      hadithCollection[1], // Manners - Abu Huraira
    ],
  },
];

// ─── Benchmark Data ───────────────────────────────────────────
export const benchmarkData: BenchmarkEntry[] = [
  {
    algorithmName: 'Cross-Encoder',
    map: 0.842,
    precisionAt10: 0.910,
    recallAt100: 0.876,
    ndcg: 0.865,
  },
  {
    algorithmName: 'BM25 (Lucene)',
    map: 0.654,
    precisionAt10: 0.740,
    recallAt100: 0.712,
    ndcg: 0.689,
  },
  {
    algorithmName: 'Neural Bi-Encoder',
    map: 0.721,
    precisionAt10: 0.820,
    recallAt100: 0.795,
    ndcg: 0.758,
  },
  {
    algorithmName: 'TF-IDF',
    map: 0.589,
    precisionAt10: 0.680,
    recallAt100: 0.654,
    ndcg: 0.623,
  },
  {
    algorithmName: 'DPR',
    map: 0.698,
    precisionAt10: 0.790,
    recallAt100: 0.768,
    ndcg: 0.734,
  },
];

// ─── Popular Search Tags ──────────────────────────────────────
export const popularSearches = [
  'Prayer times',
  'Purification',
  'Fasting Ramadan',
  'Zakat',
  'Hajj pilgrimage',
  'Marriage',
  'Inheritance',
  'Mercy',
  'Forgiveness',
  'Knowledge',
];

// ─── Grade Labels & Colors ────────────────────────────────────
export const gradeConfig: Record<string, { label: string; bgClass: string; textClass: string; hex: string }> = {
  'sahih': { label: 'Sahih', bgClass: 'bg-grade-sahih', textClass: 'text-white', hex: '#005129' },
  'hasan-sahih': { label: 'Hasan Sahih', bgClass: 'bg-grade-hasan-sahih', textClass: 'text-white', hex: '#2d8a4e' },
  'hasan': { label: 'Hasan', bgClass: 'bg-grade-hasan', textClass: 'text-white', hex: '#9a7b00' },
  'daif-hasan': { label: "Da'if Hasan", bgClass: 'bg-grade-daif-hasan', textClass: 'text-white', hex: '#c45000' },
  'daif': { label: "Da'if", bgClass: 'bg-grade-daif', textClass: 'text-white', hex: '#93000a' },
};
