const currencies = {
  MYR: 4.72,
  KRW: 1375,
  USD: 1,
  SGD: 1.35,
  JPY: 157,
  EUR: 0.92,
  GBP: 0.78,
  AUD: 1.5,
  CAD: 1.37,
  THB: 36.7,
  IDR: 16200,
  PHP: 58.6,
  VND: 25400,
  CNY: 7.24,
  INR: 83.4
};

const currencySymbols = {
  MYR: "RM",
  KRW: "₩",
  USD: "$",
  SGD: "S$",
  JPY: "¥",
  EUR: "€",
  GBP: "£",
  AUD: "A$",
  CAD: "C$",
  THB: "฿",
  IDR: "Rp",
  PHP: "₱",
  VND: "₫",
  CNY: "¥",
  INR: "₹"
};

const destinationData = {
  Tokyo: {
    country: "Japan",
    transport: "Use the JR Yamanote Line, Tokyo Metro day passes, and IC cards for quick transfers.",
    food: ["Tsukiji Market sushi", "Shinjuku ramen", "Harajuku crepes", "Izakaya dinner"],
    attractions: [
      { name: "Tokyo Tower", category: "Culture", cost: 22 },
      { name: "Shibuya Crossing", category: "Shopping", cost: 10 },
      { name: "Sensoji Temple", category: "Culture", cost: 8 },
      { name: "Tokyo Skytree", category: "Culture", cost: 28 },
      { name: "Akihabara", category: "Shopping", cost: 18 },
      { name: "Ueno Park", category: "Nature", cost: 12 },
      { name: "Meiji Shrine", category: "Nature", cost: 8 },
      { name: "TeamLab Planets", category: "Family", cost: 32 },
      { name: "Golden Gai", category: "Nightlife", cost: 35 }
    ]
  },
  Osaka: {
    country: "Japan",
    transport: "Base yourself near Namba or Umeda and use Osaka Metro with short train hops to Kyoto or Nara.",
    food: ["Dotonbori takoyaki", "Okonomiyaki dinner", "Kuromon Market snacks", "Kushikatsu"],
    attractions: [
      { name: "Osaka Castle", category: "Culture", cost: 12 },
      { name: "Dotonbori", category: "Food", cost: 20 },
      { name: "Osaka Aquarium", category: "Family", cost: 25 },
      { name: "Shinsekai", category: "Food", cost: 18 },
      { name: "Universal Studios Japan", category: "Family", cost: 85 },
      { name: "Namba Parks", category: "Shopping", cost: 15 },
      { name: "Minoo Park", category: "Nature", cost: 10 }
    ]
  },
  Seoul: {
    country: "South Korea",
    transport: "Use T-money cards, subway line transfers, and taxis after late-night meals.",
    food: ["Gwangjang Market", "Hongdae barbecue", "Myeongdong street food", "Cafe hopping"],
    attractions: [
      { name: "Gyeongbokgung Palace", category: "Culture", cost: 10 },
      { name: "Bukchon Hanok Village", category: "Culture", cost: 6 },
      { name: "N Seoul Tower", category: "Nature", cost: 22 },
      { name: "Myeongdong", category: "Shopping", cost: 25 },
      { name: "Hongdae", category: "Nightlife", cost: 35 },
      { name: "Lotte World", category: "Family", cost: 62 },
      { name: "Hangang Park", category: "Nature", cost: 12 }
    ]
  },
  Bali: {
    country: "Indonesia",
    transport: "Hire a private driver for full-day routes and use scooters only where traffic feels comfortable.",
    food: ["Nasi campur", "Jimbaran seafood", "Ubud cafes", "Warung lunch"],
    attractions: [
      { name: "Ubud Rice Terraces", category: "Nature", cost: 14 },
      { name: "Uluwatu Temple", category: "Culture", cost: 12 },
      { name: "Seminyak Beach", category: "Nature", cost: 18 },
      { name: "Tegenungan Waterfall", category: "Nature", cost: 10 },
      { name: "Ubud Art Market", category: "Shopping", cost: 20 },
      { name: "Mount Batur Sunrise", category: "Nature", cost: 45 },
      { name: "Canggu Cafes", category: "Food", cost: 22 }
    ]
  },
  Bangkok: {
    country: "Thailand",
    transport: "Combine BTS Skytrain, river boats, and ride-hailing for markets and temple districts.",
    food: ["Boat noodles", "Yaowarat seafood", "Pad thai", "Mango sticky rice"],
    attractions: [
      { name: "Grand Palace", category: "Culture", cost: 18 },
      { name: "Wat Arun", category: "Culture", cost: 8 },
      { name: "Chatuchak Market", category: "Shopping", cost: 25 },
      { name: "Chao Phraya River", category: "Nature", cost: 12 },
      { name: "Siam Paragon", category: "Shopping", cost: 20 },
      { name: "Khao San Road", category: "Nightlife", cost: 30 },
      { name: "Lumphini Park", category: "Nature", cost: 7 }
    ]
  },
  Paris: {
    country: "France",
    transport: "Use Metro carnet passes, walk central neighborhoods, and reserve longer museum visits in advance.",
    food: ["Croissant breakfast", "Bistro lunch", "Marais falafel", "Seine picnic"],
    attractions: [
      { name: "Eiffel Tower", category: "Culture", cost: 35 },
      { name: "Louvre Museum", category: "Culture", cost: 25 },
      { name: "Montmartre", category: "Culture", cost: 12 },
      { name: "Seine River Cruise", category: "Nature", cost: 22 },
      { name: "Le Marais", category: "Shopping", cost: 18 },
      { name: "Versailles", category: "Culture", cost: 42 },
      { name: "Latin Quarter", category: "Food", cost: 25 }
    ]
  },
  Singapore: {
    country: "Singapore",
    transport: "Use MRT and buses with contactless payment; rides are short and predictable.",
    food: ["Maxwell Food Centre", "Laksa", "Chilli crab", "Kaya toast"],
    attractions: [
      { name: "Gardens by the Bay", category: "Nature", cost: 28 },
      { name: "Marina Bay Sands", category: "Shopping", cost: 25 },
      { name: "Sentosa Island", category: "Family", cost: 55 },
      { name: "Chinatown", category: "Food", cost: 18 },
      { name: "Singapore Zoo", category: "Family", cost: 38 },
      { name: "Little India", category: "Culture", cost: 12 },
      { name: "Jewel Changi", category: "Shopping", cost: 15 }
    ]
  },
  "New York": {
    country: "United States",
    transport: "Use OMNY for subway and buses, walk neighborhood clusters, and avoid peak taxi times.",
    food: ["Bagels", "Pizza slice", "Chelsea Market", "Koreatown dinner"],
    attractions: [
      { name: "Central Park", category: "Nature", cost: 10 },
      { name: "Statue of Liberty", category: "Culture", cost: 30 },
      { name: "Times Square", category: "Shopping", cost: 12 },
      { name: "Met Museum", category: "Culture", cost: 30 },
      { name: "Brooklyn Bridge", category: "Nature", cost: 8 },
      { name: "Broadway Show", category: "Nightlife", cost: 110 },
      { name: "SoHo", category: "Shopping", cost: 35 }
    ]
  },
  London: {
    country: "United Kingdom",
    transport: "Use the Tube with contactless payment, walk central sights, and book airport rail early.",
    food: ["Borough Market", "Sunday roast", "Afternoon tea", "Brick Lane curry"],
    attractions: [
      { name: "Tower Bridge", category: "Culture", cost: 15 },
      { name: "British Museum", category: "Culture", cost: 10 },
      { name: "London Eye", category: "Family", cost: 38 },
      { name: "Camden Market", category: "Shopping", cost: 22 },
      { name: "Hyde Park", category: "Nature", cost: 8 },
      { name: "West End Show", category: "Nightlife", cost: 95 },
      { name: "Buckingham Palace", category: "Culture", cost: 18 }
    ]
  },
  Rome: {
    country: "Italy",
    transport: "Walk historic districts, use metro for longer hops, and reserve major ruins ahead.",
    food: ["Carbonara", "Roman pizza", "Gelato", "Trastevere trattoria"],
    attractions: [
      { name: "Colosseum", category: "Culture", cost: 28 },
      { name: "Vatican Museums", category: "Culture", cost: 35 },
      { name: "Trevi Fountain", category: "Culture", cost: 8 },
      { name: "Trastevere", category: "Food", cost: 24 },
      { name: "Villa Borghese", category: "Nature", cost: 12 },
      { name: "Campo de Fiori", category: "Shopping", cost: 18 }
    ]
  },
  Barcelona: {
    country: "Spain",
    transport: "Use metro T-casual tickets, walk Gothic Quarter routes, and prebook Gaudi sights.",
    food: ["Tapas", "Paella", "La Boqueria snacks", "Churros"],
    attractions: [
      { name: "Sagrada Familia", category: "Culture", cost: 32 },
      { name: "Park Guell", category: "Nature", cost: 18 },
      { name: "Gothic Quarter", category: "Culture", cost: 10 },
      { name: "La Boqueria", category: "Food", cost: 22 },
      { name: "Barceloneta Beach", category: "Nature", cost: 12 },
      { name: "Passeig de Gracia", category: "Shopping", cost: 24 }
    ]
  },
  Amsterdam: {
    country: "Netherlands",
    transport: "Use trams, ferries, and bikes where comfortable; reserve museums before arrival.",
    food: ["Stroopwafels", "Dutch pancakes", "Foodhallen", "Canal-side cafes"],
    attractions: [
      { name: "Rijksmuseum", category: "Culture", cost: 25 },
      { name: "Van Gogh Museum", category: "Culture", cost: 27 },
      { name: "Canal Cruise", category: "Nature", cost: 20 },
      { name: "Jordaan", category: "Food", cost: 18 },
      { name: "Vondelpark", category: "Nature", cost: 8 },
      { name: "Nine Streets", category: "Shopping", cost: 20 }
    ]
  },
  Istanbul: {
    country: "Turkey",
    transport: "Use Istanbulkart for trams, ferries, metro, and buses across both continents.",
    food: ["Turkish breakfast", "Kebabs", "Baklava", "Balik ekmek"],
    attractions: [
      { name: "Hagia Sophia", category: "Culture", cost: 18 },
      { name: "Blue Mosque", category: "Culture", cost: 8 },
      { name: "Grand Bazaar", category: "Shopping", cost: 24 },
      { name: "Bosphorus Cruise", category: "Nature", cost: 22 },
      { name: "Galata Tower", category: "Culture", cost: 20 },
      { name: "Karakoy", category: "Food", cost: 20 }
    ]
  },
  Dubai: {
    country: "United Arab Emirates",
    transport: "Use metro for the main corridor, taxis for beach districts, and booked transfers for desert trips.",
    food: ["Arabic mezze", "Shawarma", "Emirati machboos", "Marina dining"],
    attractions: [
      { name: "Burj Khalifa", category: "Culture", cost: 55 },
      { name: "Dubai Mall", category: "Shopping", cost: 30 },
      { name: "Desert Safari", category: "Nature", cost: 75 },
      { name: "Dubai Marina", category: "Nightlife", cost: 35 },
      { name: "Museum of the Future", category: "Family", cost: 42 },
      { name: "Jumeirah Beach", category: "Nature", cost: 14 }
    ]
  },
  Cairo: {
    country: "Egypt",
    transport: "Hire licensed drivers for pyramid days and use ride-hailing for museum and Nile routes.",
    food: ["Koshari", "Ful medames", "Grilled kofta", "Nile dinner"],
    attractions: [
      { name: "Giza Pyramids", category: "Culture", cost: 30 },
      { name: "Egyptian Museum", category: "Culture", cost: 18 },
      { name: "Khan el-Khalili", category: "Shopping", cost: 16 },
      { name: "Nile Felucca", category: "Nature", cost: 20 },
      { name: "Coptic Cairo", category: "Culture", cost: 10 },
      { name: "Al-Azhar Park", category: "Nature", cost: 8 }
    ]
  },
  "Cape Town": {
    country: "South Africa",
    transport: "Use ride-hailing in the city and book day tours for wine country or peninsula routes.",
    food: ["Cape Malay curry", "Seafood", "Wine estate lunch", "Braaied meats"],
    attractions: [
      { name: "Table Mountain", category: "Nature", cost: 35 },
      { name: "V&A Waterfront", category: "Shopping", cost: 22 },
      { name: "Robben Island", category: "Culture", cost: 32 },
      { name: "Boulders Beach", category: "Nature", cost: 14 },
      { name: "Bo-Kaap", category: "Culture", cost: 10 },
      { name: "Kirstenbosch Garden", category: "Nature", cost: 16 }
    ]
  },
  Marrakech: {
    country: "Morocco",
    transport: "Walk medina routes with offline maps and use private drivers for desert or Atlas day trips.",
    food: ["Tagine", "Mint tea", "Couscous", "Jemaa el-Fnaa snacks"],
    attractions: [
      { name: "Jemaa el-Fnaa", category: "Culture", cost: 18 },
      { name: "Majorelle Garden", category: "Nature", cost: 16 },
      { name: "Bahia Palace", category: "Culture", cost: 12 },
      { name: "Souks of Marrakech", category: "Shopping", cost: 24 },
      { name: "Atlas Mountains", category: "Nature", cost: 55 },
      { name: "Medina Food Tour", category: "Food", cost: 38 }
    ]
  },
  Sydney: {
    country: "Australia",
    transport: "Use Opal/contactless cards for ferries, trains, and buses; ferry rides are part of the experience.",
    food: ["Flat white cafes", "Fish and chips", "Thai town dinner", "Brunch"],
    attractions: [
      { name: "Sydney Opera House", category: "Culture", cost: 38 },
      { name: "Harbour Bridge", category: "Nature", cost: 20 },
      { name: "Bondi Beach", category: "Nature", cost: 12 },
      { name: "Taronga Zoo", category: "Family", cost: 48 },
      { name: "The Rocks", category: "Food", cost: 24 },
      { name: "Queen Victoria Building", category: "Shopping", cost: 18 }
    ]
  },
  Queenstown: {
    country: "New Zealand",
    transport: "Book shuttles for adventure activities and consider a rental car for lake and mountain routes.",
    food: ["Fergburger", "Lakefront cafes", "Pinot noir tasting", "Bakery breakfast"],
    attractions: [
      { name: "Lake Wakatipu", category: "Nature", cost: 10 },
      { name: "Skyline Gondola", category: "Family", cost: 42 },
      { name: "Milford Sound", category: "Nature", cost: 120 },
      { name: "Arrowtown", category: "Culture", cost: 16 },
      { name: "Shotover Jet", category: "Family", cost: 95 },
      { name: "Queenstown Gardens", category: "Nature", cost: 8 }
    ]
  },
  "Rio de Janeiro": {
    country: "Brazil",
    transport: "Use metro for beach zones, ride-hailing at night, and guided transfers for hilltop sights.",
    food: ["Feijoada", "Acai bowls", "Churrasco", "Beach kiosks"],
    attractions: [
      { name: "Christ the Redeemer", category: "Culture", cost: 32 },
      { name: "Sugarloaf Mountain", category: "Nature", cost: 34 },
      { name: "Copacabana Beach", category: "Nature", cost: 14 },
      { name: "Ipanema", category: "Shopping", cost: 20 },
      { name: "Lapa", category: "Nightlife", cost: 28 },
      { name: "Selaron Steps", category: "Culture", cost: 10 }
    ]
  },
  "Mexico City": {
    country: "Mexico",
    transport: "Use ride-hailing for long hops, Metrobus in central corridors, and guided trips to ruins.",
    food: ["Tacos al pastor", "Churros", "Roma Norte cafes", "Mole"],
    attractions: [
      { name: "Frida Kahlo Museum", category: "Culture", cost: 18 },
      { name: "Chapultepec Park", category: "Nature", cost: 10 },
      { name: "Teotihuacan", category: "Culture", cost: 48 },
      { name: "Zocalo", category: "Culture", cost: 8 },
      { name: "Roma Norte", category: "Food", cost: 25 },
      { name: "La Ciudadela Market", category: "Shopping", cost: 18 }
    ]
  },
  Vancouver: {
    country: "Canada",
    transport: "Use SkyTrain and buses, with ferry or shuttle add-ons for mountain and island days.",
    food: ["Sushi", "Granville Island bites", "Poutine", "Coffee roasters"],
    attractions: [
      { name: "Stanley Park", category: "Nature", cost: 12 },
      { name: "Granville Island", category: "Food", cost: 24 },
      { name: "Capilano Suspension Bridge", category: "Nature", cost: 58 },
      { name: "Gastown", category: "Culture", cost: 12 },
      { name: "Grouse Mountain", category: "Family", cost: 65 },
      { name: "Robson Street", category: "Shopping", cost: 20 }
    ]
  },
  "Los Angeles": {
    country: "United States",
    transport: "Plan routes by neighborhood, use ride-hailing selectively, and allow time for traffic.",
    food: ["Tacos", "Koreatown barbecue", "Santa Monica seafood", "Food trucks"],
    attractions: [
      { name: "Griffith Observatory", category: "Nature", cost: 12 },
      { name: "Hollywood Walk of Fame", category: "Culture", cost: 10 },
      { name: "Santa Monica Pier", category: "Family", cost: 24 },
      { name: "Getty Center", category: "Culture", cost: 15 },
      { name: "Rodeo Drive", category: "Shopping", cost: 28 },
      { name: "Venice Beach", category: "Nature", cost: 14 }
    ]
  },
  "Buenos Aires": {
    country: "Argentina",
    transport: "Use Subte for central routes, taxis at night, and walk compact neighborhoods.",
    food: ["Steak dinner", "Empanadas", "Dulce de leche", "Cafe notable"],
    attractions: [
      { name: "La Boca", category: "Culture", cost: 14 },
      { name: "Recoleta Cemetery", category: "Culture", cost: 12 },
      { name: "San Telmo Market", category: "Shopping", cost: 20 },
      { name: "Palermo Parks", category: "Nature", cost: 10 },
      { name: "Tango Show", category: "Nightlife", cost: 70 },
      { name: "Puerto Madero", category: "Food", cost: 26 }
    ]
  },
  Lima: {
    country: "Peru",
    transport: "Use ride-hailing between districts and book guided transfers for ruins or coastal trips.",
    food: ["Ceviche", "Lomo saltado", "Picarones", "Barranco tasting menus"],
    attractions: [
      { name: "Miraflores", category: "Nature", cost: 14 },
      { name: "Larco Museum", category: "Culture", cost: 16 },
      { name: "Barranco", category: "Food", cost: 24 },
      { name: "Huaca Pucllana", category: "Culture", cost: 12 },
      { name: "Larcomar", category: "Shopping", cost: 20 },
      { name: "Magic Water Circuit", category: "Family", cost: 8 }
    ]
  },
  Santorini: {
    country: "Greece",
    transport: "Use buses between villages, book transfers for late nights, and reserve sunset dining early.",
    food: ["Greek salad", "Seafood", "Fava", "Winery lunch"],
    attractions: [
      { name: "Oia Sunset", category: "Nature", cost: 14 },
      { name: "Fira", category: "Shopping", cost: 20 },
      { name: "Red Beach", category: "Nature", cost: 12 },
      { name: "Akrotiri", category: "Culture", cost: 18 },
      { name: "Caldera Cruise", category: "Family", cost: 75 },
      { name: "Santorini Winery", category: "Food", cost: 36 }
    ]
  },
  "Kuala Lumpur": {
    country: "Malaysia",
    transport: "Use MRT/LRT for city routes and ride-hailing for food districts or late evenings.",
    food: ["Nasi lemak", "Roti canai", "Jalan Alor snacks", "Banana leaf rice"],
    attractions: [
      { name: "Petronas Twin Towers", category: "Culture", cost: 25 },
      { name: "Batu Caves", category: "Culture", cost: 12 },
      { name: "Bukit Bintang", category: "Shopping", cost: 22 },
      { name: "KLCC Park", category: "Nature", cost: 8 },
      { name: "Jalan Alor", category: "Food", cost: 18 },
      { name: "Aquaria KLCC", category: "Family", cost: 20 }
    ]
  },
  Hanoi: {
    country: "Vietnam",
    transport: "Walk the Old Quarter carefully, use ride-hailing, and book day trips for bay or countryside routes.",
    food: ["Pho", "Bun cha", "Egg coffee", "Banh mi"],
    attractions: [
      { name: "Old Quarter", category: "Culture", cost: 10 },
      { name: "Hoan Kiem Lake", category: "Nature", cost: 8 },
      { name: "Temple of Literature", category: "Culture", cost: 8 },
      { name: "Train Street", category: "Food", cost: 12 },
      { name: "Dong Xuan Market", category: "Shopping", cost: 16 },
      { name: "Ha Long Bay Day Trip", category: "Nature", cost: 70 }
    ]
  }
};

function makeDestination(country, landmark, market, nature, dish, city) {
  return {
    country,
    transport: `Use central public transport and walking routes in ${city}; reserve intercity or airport transfers early for smoother travel.`,
    food: [dish, "Old town cafe stops", "Local market snacks", "Traditional dinner"],
    attractions: [
      { name: landmark, category: "Culture", cost: 24 },
      { name: market, category: "Shopping", cost: 18 },
      { name: nature, category: "Nature", cost: 16 },
      { name: `${city} Old Town`, category: "Culture", cost: 12 },
      { name: `${city} Food Walk`, category: "Food", cost: 28 },
      { name: `${city} Evening Quarter`, category: "Nightlife", cost: 26 }
    ]
  };
}

const expandedDestinations = [
  ["Hong Kong", "Hong Kong", "Victoria Peak", "Temple Street Night Market", "Victoria Harbour", "Dim sum"],
  ["Bandar Seri Begawan", "Brunei", "Omar Ali Saifuddien Mosque", "Gadong Night Market", "Kampong Ayer", "Ambuyat"],
  ["Phnom Penh", "Cambodia", "Royal Palace", "Central Market", "Mekong Riverside", "Fish amok"],
  ["Jakarta", "Indonesia", "National Monument", "Grand Indonesia", "Ancol Beach", "Nasi goreng"],
  ["Vientiane", "Laos", "Pha That Luang", "Talat Sao Market", "Mekong Riverfront", "Laap"],
  ["Manila", "Philippines", "Intramuros", "Divisoria Market", "Manila Bay", "Adobo"],
  ["Naypyidaw", "Myanmar", "Uppatasanti Pagoda", "Myoma Market", "Naypyidaw Water Fountain Garden", "Mohinga"],
  ["Dili", "Timor-Leste", "Cristo Rei of Dili", "Tais Market", "Areia Branca Beach", "Ikan sabuko"],
  ["Vienna", "Austria", "Schonbrunn Palace", "Naschmarkt", "Stadtpark", "Wiener schnitzel"],
  ["Tirana", "Albania", "Skanderbeg Square", "New Bazaar", "Grand Park of Tirana", "Byrek"],
  ["Andorra la Vella", "Andorra", "Casa de la Vall", "Avinguda Meritxell", "Madriu Valley", "Trinxat"],
  ["Yerevan", "Armenia", "Cascade Complex", "Vernissage Market", "Hrazdan Gorge", "Khorovats"],
  ["Baku", "Azerbaijan", "Flame Towers", "Nizami Street", "Baku Boulevard", "Plov"],
  ["Minsk", "Belarus", "Independence Square", "Komarovka Market", "Gorky Park", "Draniki"],
  ["Brussels", "Belgium", "Grand Place", "Galeries Royales Saint-Hubert", "Parc de Bruxelles", "Belgian waffles"],
  ["Sarajevo", "Bosnia and Herzegovina", "Bascarsija", "Gazi Husrev-beg Bazaar", "Vrelo Bosne", "Cevapi"],
  ["Sofia", "Bulgaria", "Alexander Nevsky Cathedral", "Vitosha Boulevard", "Borisova Gradina", "Banitsa"],
  ["Zagreb", "Croatia", "St Mark's Church", "Dolac Market", "Maksimir Park", "Strukli"],
  ["Nicosia", "Cyprus", "Ledra Street", "Municipal Market", "Athalassa Park", "Halloumi mezze"],
  ["Prague", "Czech Republic", "Prague Castle", "Old Town Square", "Letna Park", "Goulash"],
  ["Copenhagen", "Denmark", "Nyhavn", "Stroget", "Tivoli Gardens", "Smorrebrod"],
  ["Tallinn", "Estonia", "Toompea Castle", "Balti Jaama Market", "Kadriorg Park", "Black bread tasting"],
  ["Helsinki", "Finland", "Helsinki Cathedral", "Market Square", "Esplanadi Park", "Salmon soup"],
  ["Tbilisi", "Georgia", "Narikala Fortress", "Dry Bridge Market", "Mtatsminda Park", "Khachapuri"],
  ["Berlin", "Germany", "Brandenburg Gate", "Kurfurstendamm", "Tiergarten", "Currywurst"],
  ["Athens", "Greece", "Acropolis", "Monastiraki Flea Market", "National Garden", "Souvlaki"],
  ["Budapest", "Hungary", "Buda Castle", "Great Market Hall", "Margaret Island", "Goulash soup"],
  ["Reykjavik", "Iceland", "Hallgrimskirkja", "Laugavegur", "Sun Voyager Waterfront", "Icelandic lamb"],
  ["Dublin", "Ireland", "Trinity College", "Grafton Street", "St Stephen's Green", "Irish stew"],
  ["Pristina", "Kosovo", "Newborn Monument", "Old Bazaar", "Germia Park", "Flija"],
  ["Riga", "Latvia", "House of the Blackheads", "Central Market", "Bastejkalna Park", "Rye bread snacks"],
  ["Vaduz", "Liechtenstein", "Vaduz Castle", "Stadtle", "Rhine Valley", "Kasknopfle"],
  ["Vilnius", "Lithuania", "Gediminas Tower", "Hales Market", "Bernardine Garden", "Cepelinai"],
  ["Luxembourg City", "Luxembourg", "Bock Casemates", "Place d'Armes", "Petrusse Valley", "Judd mat Gaardebounen"],
  ["Valletta", "Malta", "St John's Co-Cathedral", "Merchant Street", "Upper Barrakka Gardens", "Pastizzi"],
  ["Chisinau", "Moldova", "Nativity Cathedral", "Central Market", "Valea Morilor Park", "Placinte"],
  ["Monaco", "Monaco", "Prince's Palace", "Monte Carlo", "Larvotto Beach", "Barbajuan"],
  ["Podgorica", "Montenegro", "Millennium Bridge", "Bokeska Street", "Moraca River", "Cicvara"],
  ["Skopje", "North Macedonia", "Stone Bridge", "Old Bazaar", "Vodno Mountain", "Tavce gravce"],
  ["Oslo", "Norway", "Oslo Opera House", "Aker Brygge", "Vigeland Park", "Norwegian salmon"],
  ["Warsaw", "Poland", "Royal Castle", "Nowy Swiat", "Lazienki Park", "Pierogi"],
  ["Lisbon", "Portugal", "Belem Tower", "Time Out Market", "Miradouro da Senhora do Monte", "Pastel de nata"],
  ["Bucharest", "Romania", "Palace of Parliament", "Lipscani", "Cismigiu Gardens", "Sarmale"],
  ["San Marino", "San Marino", "Guaita Tower", "Historic Centre Shops", "Monte Titano", "Piadina"],
  ["Belgrade", "Serbia", "Belgrade Fortress", "Knez Mihailova", "Kalemegdan Park", "Pljeskavica"],
  ["Bratislava", "Slovakia", "Bratislava Castle", "Old Market Hall", "Danube Promenade", "Bryndzove halusky"],
  ["Ljubljana", "Slovenia", "Ljubljana Castle", "Central Market", "Tivoli Park", "Potica"],
  ["Stockholm", "Sweden", "Royal Palace", "Ostermalm Market Hall", "Djurgarden", "Swedish meatballs"],
  ["Zurich", "Switzerland", "Grossmunster", "Bahnhofstrasse", "Lake Zurich", "Rosti"],
  ["Kyiv", "Ukraine", "St Sophia's Cathedral", "Andriyivskyy Descent", "Mariinsky Park", "Borscht"],
  ["Vatican City", "Vatican City", "St Peter's Basilica", "Vatican Museum Shop", "Vatican Gardens", "Roman trattoria meal"],
  ["Moscow", "Russia", "Red Square", "GUM", "Zaryadye Park", "Borscht and blini"]
];

expandedDestinations.forEach(([city, country, landmark, market, nature, dish]) => {
  if (!destinationData[city]) {
    destinationData[city] = makeDestination(country, landmark, market, nature, dish, city);
  }
});

const destinationAliases = {
  hongkong: "Hong Kong",
  uae: "Dubai",
  unitedarabemirates: "Dubai",
  turkey: "Istanbul",
  turkiye: "Istanbul",
  uk: "London",
  england: "London",
  greatbritain: "London",
  czechia: "Prague",
  holland: "Amsterdam",
  burma: "Naypyidaw",
  laos: "Vientiane",
  timorleste: "Dili"
};

const times = ["08:00", "10:00", "12:00", "14:00", "17:00", "20:00"];
const storageKeys = {
  saved: "travelgenie.savedTrips",
  recent: "travelgenie.recentTrips"
};

const state = {
  currentTrip: null,
  listMode: "saved",
  isLoggedIn: false,
  user: null
};

const destinationInput = document.querySelector("#destination");
const heroDestinationInput = document.querySelector("#hero-destination");
const suggestionBox = document.querySelector("#destination-suggestions");
const destinationMessage = document.querySelector("#destination-message");
const customPlacesInput = document.querySelector("#custom-places");
const currencySelect = document.querySelector("#currency");
const tripForm = document.querySelector("#trip-form");
const resultSection = document.querySelector("#result");
const tripList = document.querySelector("#trip-list");
const savedCount = document.querySelector("#saved-count");
const recentCount = document.querySelector("#recent-count");
const budgetTip = document.querySelector("#budget-tip");
const navToggle = document.querySelector(".nav-toggle");
const toast = document.querySelector("#toast");
const adminDestinations = document.querySelector("#admin-destinations");
const adminAttractions = document.querySelector("#admin-attractions");

function init() {
  populateCurrencies();
  applyAuthState();
  showAuthRedirectMessage();
  refreshSession();
  updateBudgetTip();
  updateAdminStats();
  updateCounts();
  renderTripList();
  bindEvents();
}

function bindEvents() {
  navToggle.addEventListener("click", () => {
    const isOpen = document.body.classList.toggle("nav-open");
    navToggle.setAttribute("aria-expanded", String(isOpen));
  });

  document.querySelectorAll(".site-nav a").forEach((link) => {
    link.addEventListener("click", () => document.body.classList.remove("nav-open"));
  });

  document.querySelector("[data-jump-planner]").addEventListener("submit", (event) => {
    event.preventDefault();
    if (!state.isLoggedIn) {
      openAuth("login");
      return;
    }
    if (heroDestinationInput.value.trim()) {
      destinationInput.value = normalizeDestination(heroDestinationInput.value.trim());
      updateBudgetTip();
    }
    document.querySelector("#planner").scrollIntoView({ behavior: "smooth" });
    destinationInput.focus();
  });

  destinationInput.addEventListener("input", handleDestinationInput);
  destinationInput.addEventListener("blur", () => setTimeout(() => suggestionBox.classList.remove("active"), 160));
  destinationInput.addEventListener("change", () => {
    updateBudgetTip();
  });

  tripForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!state.isLoggedIn) {
      openAuth("login");
      return;
    }
    const submitButton = tripForm.querySelector("[type='submit']");
    const originalLabel = submitButton.textContent;
    submitButton.disabled = true;
    submitButton.textContent = "Generating...";
    resultSection.innerHTML = `<div class="empty-result"><h2>Generating your itinerary</h2><p>Gemini is arranging the route, budget, meals, and daily timing.</p></div>`;
    resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
    try {
      const trip = await buildTrip(new FormData(tripForm));
      state.currentTrip = trip;
      saveRecentTrip(trip);
      renderResult(trip);
      updateCounts();
      renderTripList();
    } catch (error) {
      resultSection.innerHTML = `<div class="empty-result"><h2>Could not generate itinerary</h2><p>${escapeHtml(
        error.message
      )}</p></div>`;
      showToast(error.message);
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = originalLabel;
    }
  });

  tripForm.addEventListener("reset", () => {
    setTimeout(() => {
      destinationMessage.textContent = "";
      updateBudgetTip();
    }, 0);
  });

  document.querySelector("#show-saved").addEventListener("click", () => {
    state.listMode = "saved";
    renderTripList();
  });

  document.querySelector("#show-recent").addEventListener("click", () => {
    state.listMode = "recent";
    renderTripList();
  });

  document.querySelectorAll("[data-auth-open]").forEach((button) => {
    button.addEventListener("click", () => openAuth(button.dataset.authOpen));
  });

  document.querySelectorAll("[data-auth-tab]").forEach((button) => {
    button.addEventListener("click", () => switchAuthTab(button.dataset.authTab));
  });

  document.querySelector("#login-demo").addEventListener("click", emailAuthUnavailable);
  document.querySelector("#register-demo").addEventListener("click", emailAuthUnavailable);
  document.querySelectorAll("[data-google-auth]").forEach((button) => {
    button.addEventListener("click", startGoogleAuth);
  });
  document.querySelector("#logout-button").addEventListener("click", logoutUser);
  document.querySelector("#nav-logout-button").addEventListener("click", logoutUser);
}

function populateCurrencies() {
  Object.keys(currencies).forEach((code) => {
    const option = document.createElement("option");
    option.value = code;
    option.textContent = code;
    if (code === "USD") option.selected = true;
    currencySelect.append(option);
  });
}

function handleDestinationInput() {
  const query = destinationInput.value.trim().toLowerCase();
  suggestionBox.innerHTML = "";
  destinationMessage.textContent = "";

  if (!query) {
    suggestionBox.classList.remove("active");
    return;
  }

  const suggestions = getSuggestions(query);
  if (!suggestions.length) {
    destinationMessage.textContent = "Gemini can plan this destination. Add any must-visit places below.";
    suggestionBox.classList.remove("active");
    return;
  }

  suggestions.forEach((suggestion) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = suggestion;
    button.addEventListener("mousedown", () => {
      destinationInput.value = normalizeDestination(suggestion);
      updateBudgetTip();
      suggestionBox.classList.remove("active");
    });
    suggestionBox.append(button);
  });
  suggestionBox.classList.add("active");
}

function getSuggestions(query) {
  const normalizedQuery = searchKey(query);
  const destinations = Object.entries(destinationData);
  const destinationMatches = destinations
    .filter(([name, details]) => {
      const searchable = searchKey(`${name} ${details.country}`);
      return searchable.includes(normalizedQuery);
    })
    .map(([name, details]) => `${name}, ${details.country}`);

  const aliasMatches = Object.entries(destinationAliases)
    .filter(([alias]) => alias.includes(normalizedQuery))
    .map(([, city]) => `${city}, ${destinationData[city].country}`);

  const attractionMatches = destinations.flatMap(([city, details]) =>
    details.attractions
      .filter((attraction) => searchKey(attraction.name).includes(normalizedQuery))
      .map((attraction) => `${attraction.name}, ${city}`)
  );

  return [...new Set([...destinationMatches, ...aliasMatches, ...attractionMatches])].slice(0, 9);
}

function normalizeDestination(value) {
  const cleaned = value.split(",")[0].trim();
  const cleanedKey = searchKey(cleaned);
  if (destinationAliases[cleanedKey]) return destinationAliases[cleanedKey];

  const direct = Object.keys(destinationData).find((name) => searchKey(name) === cleanedKey);
  if (direct) return direct;

  const fromCountry = Object.entries(destinationData).find(([, details]) => searchKey(details.country) === cleanedKey);
  if (fromCountry) return fromCountry[0];

  const fromAttraction = Object.entries(destinationData).find(([, details]) =>
    details.attractions.some((attraction) => cleanedKey.includes(searchKey(attraction.name)))
  );
  return fromAttraction ? fromAttraction[0] : value;
}

function searchKey(value) {
  return String(value).toLowerCase().replace(/[^a-z0-9]/g, "");
}

function getDestination(value) {
  const normalized = normalizeDestination(value || "Tokyo");
  if (destinationData[normalized]) return { name: normalized, ...destinationData[normalized] };
  return { name: value || "Tokyo", country: "", transport: "", food: [], attractions: [] };
}

function updateBudgetTip() {
  const data = getDestination(destinationInput.value);
  const place = data.country ? `${data.name}, ${data.country}` : data.name;
  budgetTip.textContent = `${place}: Gemini will adapt the budget to your selected style and requested places.`;
}

async function buildTrip(formData) {
  const destination = formData.get("destination").trim();
  const budget = Number(formData.get("budget"));
  const currency = formData.get("currency");
  const travelers = Number(formData.get("travelers"));
  const days = Number(formData.get("days"));
  const interests = formData.getAll("interests");
  const budgetStyle = formData.get("budgetStyle");
  const customPlaces = parseCustomPlaces(formData.get("customPlaces"));
  const tripName = formData.get("tripName").trim() || `${destination} ${days}-Day Trip`;
  const request = { destination, budget, currency, travelers, days, interests, budgetStyle, customPlaces, tripName };
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 35000);
  let response;
  try {
    response = await fetch("/api/itinerary", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
      signal: controller.signal
    });
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("Gemini took too long to respond. Please try a shorter trip or try again.");
    }
    throw new Error("The itinerary server could not be reached.");
  } finally {
    clearTimeout(timeout);
  }

  {
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      const messages = {
        unauthorized: "Please log in before generating an itinerary.",
        missing_gemini_config: "Gemini is not configured yet. Add GEMINI_API_KEY on the server.",
        gemini_generation_failed: "Gemini could not generate the itinerary. Please check Render Logs or try again."
      };
      const detail = payload.detail ? ` ${payload.detail}` : "";
      throw new Error(`${messages[payload.error] || payload.error || "The itinerary server could not be reached."}${detail}`);
    }
    return normalizeGeneratedTrip(request, payload.itinerary || {});
  }
}

function parseCustomPlaces(value) {
  return [...new Set(String(value || "")
    .split(/[\n,;]+/)
    .map((place) => place.trim())
    .filter(Boolean))];
}

function normalizeGeneratedTrip(request, generated) {
  const destination = generated.destination || request.destination;
  const country = generated.country || "";
  return {
    id: crypto.randomUUID(),
    name: request.tripName,
    destination,
    country,
    budget: request.budget,
    currency: request.currency,
    travelers: request.travelers,
    days: request.days,
    interests: request.interests,
    budgetStyle: request.budgetStyle,
    customPlaces: request.customPlaces,
    summary: generated.summary || "",
    schedule: normalizeSchedule(generated.schedule, request),
    breakdown: normalizeBreakdown(generated.breakdown, request),
    transport: generated.transport || "Use local transit, walking routes, and ride-hailing where practical.",
    food: Array.isArray(generated.food) && generated.food.length ? generated.food : ["Local market meals", "Popular neighborhood restaurants", "Regional snacks"],
    createdAt: new Date().toISOString()
  };
}

function normalizeSchedule(schedule, request) {
  if (!Array.isArray(schedule) || !schedule.length) {
    const destination = getDestination(request.destination);
    const attractions = destination.attractions.length ? destination.attractions : [{ name: request.destination, cost: 20 }];
    return createSchedule(destination, attractions, request.days, request.travelers, request.currency);
  }
  return schedule.map((day, index) => {
    const items = Array.isArray(day.items) ? day.items : [];
    const normalizedItems = items.map((item) => ({
      time: item.time || "09:00",
      title: item.title || "Travel activity",
      notes: item.notes || "",
      cost: normalizeCost(item.cost, request.currency)
    }));
    const rawTotal = Number(day.total?.raw) || normalizedItems.reduce((sum, item) => sum + item.cost.raw, 0);
    return {
      day: Number(day.day) || index + 1,
      title: day.title || `Explore ${request.destination}`,
      items: normalizedItems,
      total: { raw: rawTotal, label: day.total?.label || formatMoney(rawTotal, request.currency) }
    };
  });
}

function createSchedule(destination, attractions, days, travelers, currency) {
  const schedule = [];
  for (let day = 1; day <= days; day += 1) {
    const dayItems = [];
    const morning = day === 1 ? "Airport Arrival" : `${destination.name} neighborhood walk`;
    dayItems.push({ time: times[0], title: morning, cost: convertCost(18 * travelers, currency) });

    for (let slot = 1; slot < times.length; slot += 1) {
      const attraction = attractions[(day + slot - 2) % attractions.length];
      const isMeal = slot === 2 || slot === 5;
      const foods = destination.food.length ? destination.food : ["Local breakfast", "Neighborhood lunch", "Regional dinner"];
      const title = isMeal
        ? `${foods[(day + slot) % foods.length]}`
        : attraction.name;
      const cost = isMeal ? 24 * travelers : attraction.cost * travelers;
      dayItems.push({ time: times[slot], title, cost: convertCost(cost, currency) });
    }

    const rawTotal = dayItems.reduce((sum, item) => sum + item.cost.raw, 0);
    schedule.push({
      day,
      title: day === 1 ? "Arrival and first highlights" : `Explore ${destination.name}`,
      items: dayItems,
      total: { raw: rawTotal, label: formatMoney(rawTotal, currency) }
    });
  }
  return schedule;
}

function convertCost(usdAmount, currency) {
  const raw = Math.round(usdAmount * currencies[currency]);
  return { raw, label: formatMoney(raw, currency) };
}

function formatMoney(amount, currency) {
  const symbol = currencySymbols[currency] || `${currency} `;
  return `${symbol}${Number(amount).toLocaleString()}`;
}

function createBudgetBreakdown(budget) {
  return [
    { label: "Accommodation", percent: 36, amount: budget * 0.36 },
    { label: "Food", percent: 20, amount: budget * 0.2 },
    { label: "Transportation", percent: 12, amount: budget * 0.12 },
    { label: "Attractions", percent: 18, amount: budget * 0.18 },
    { label: "Emergency", percent: 14, amount: budget * 0.14 }
  ];
}

function normalizeBreakdown(breakdown, request) {
  if (!Array.isArray(breakdown) || !breakdown.length) return createBudgetBreakdown(request.budget);
  return breakdown.map((item) => ({
    label: item.label || "Trip cost",
    percent: Number(item.percent) || 0,
    amount: Number(item.amount) || 0
  }));
}

function normalizeCost(cost, currency) {
  if (!cost || typeof cost !== "object") return { raw: 0, label: formatMoney(0, currency) };
  const raw = Number(cost.raw) || 0;
  return { raw, label: cost.label || formatMoney(raw, currency) };
}

function renderResult(trip) {
  const safeName = escapeHtml(trip.name);
  const safeDestination = escapeHtml(trip.destination);
  const safeCountry = escapeHtml(trip.country);
  const locationText = safeCountry ? `${safeDestination}, ${safeCountry}` : safeDestination;
  resultSection.innerHTML = `
    <article class="result-card">
      <div class="result-header">
        <div>
          <p class="eyebrow">Generated Itinerary</p>
          <h2>${safeName}</h2>
          <p>${locationText} • ${trip.days} days • ${trip.travelers} travelers • ${escapeHtml(
    trip.budgetStyle || "Comfort"
  )} • ${formatMoney(
    trip.budget,
    trip.currency
  )}</p>
          ${trip.summary ? `<p>${escapeHtml(trip.summary)}</p>` : ""}
        </div>
        <div class="result-actions">
          <button class="secondary-button" type="button" data-action="save">Save</button>
          <button class="ghost-button" type="button" data-action="rename">Rename</button>
          <button class="ghost-button" type="button" data-action="edit">Edit</button>
          <button class="ghost-button" type="button" data-action="print">Export PDF</button>
        </div>
      </div>
      <div class="result-body">
        <div class="day-list">
          ${trip.schedule.map(renderDay).join("")}
        </div>
        <aside class="result-sidebar">
          <section class="budget-card">
            <h3>Budget Breakdown</h3>
            ${trip.breakdown
              .map(
                (item) => `
                <div class="budget-row">
                  <span>${item.label}</span>
                  <strong>${formatMoney(Math.round(item.amount), trip.currency)}</strong>
                  <div class="budget-track"><span style="width: ${item.percent}%"></span></div>
                </div>`
              )
              .join("")}
          </section>
          <section class="transport-card">
            <h3>Transportation</h3>
            <p>${escapeHtml(trip.transport)}</p>
          </section>
          <section class="transport-card">
            <h3>Food Recommendations</h3>
            <p>${trip.food.map(escapeHtml).join(", ")}</p>
          </section>
          ${
            trip.customPlaces?.length
              ? `<section class="transport-card"><h3>Requested Places</h3><p>${trip.customPlaces
                  .map(escapeHtml)
                  .join(", ")}</p></section>`
              : ""
          }
        </aside>
      </div>
    </article>
  `;

  resultSection.querySelector("[data-action='save']").addEventListener("click", () => saveTrip(trip));
  resultSection.querySelector("[data-action='rename']").addEventListener("click", () => renameTrip(trip));
  resultSection.querySelector("[data-action='edit']").addEventListener("click", () => editTrip(trip));
  resultSection.querySelector("[data-action='print']").addEventListener("click", () => window.print());
}

function renderDay(day) {
  return `
    <section class="day-card">
      <h3>Day ${day.day}: ${escapeHtml(day.title)}</h3>
      <ul>
        ${day.items
          .map(
            (item) => `
          <li>
            <span class="time">${item.time}</span>
            <span>${escapeHtml(item.title)}</span>
            <span class="cost-pill">${item.cost.label}</span>
            ${item.notes ? `<small>${escapeHtml(item.notes)}</small>` : ""}
          </li>`
          )
          .join("")}
      </ul>
      <p class="trip-meta">Estimated Cost: ${day.total.label}</p>
    </section>
  `;
}

function getStoredTrips(key) {
  try {
    return JSON.parse(localStorage.getItem(key)) || [];
  } catch {
    return [];
  }
}

function setStoredTrips(key, trips) {
  localStorage.setItem(key, JSON.stringify(trips));
}

function saveRecentTrip(trip) {
  const recent = getStoredTrips(storageKeys.recent).filter((item) => item.id !== trip.id);
  setStoredTrips(storageKeys.recent, [trip, ...recent].slice(0, 6));
}

function saveTrip(trip) {
  const saved = getStoredTrips(storageKeys.saved).filter((item) => item.id !== trip.id);
  setStoredTrips(storageKeys.saved, [trip, ...saved]);
  updateCounts();
  renderTripList();
  showToast("Itinerary saved.");
}

function renameTrip(trip) {
  const name = prompt("Rename itinerary", trip.name);
  if (!name) return;
  const renamed = { ...trip, name };
  state.currentTrip = renamed;
  saveRecentTrip(renamed);
  ["saved", "recent"].forEach((type) => {
    const key = storageKeys[type];
    const trips = getStoredTrips(key).map((item) => (item.id === trip.id ? renamed : item));
    setStoredTrips(key, trips);
  });
  renderResult(renamed);
  renderTripList();
}

function editTrip(trip) {
  document.querySelector("#destination").value = trip.destination;
  document.querySelector("#budget").value = trip.budget;
  document.querySelector("#currency").value = trip.currency;
  document.querySelector("#travelers").value = trip.travelers;
  document.querySelector("#days").value = trip.days;
  document.querySelector("#trip-name").value = trip.name;
  customPlacesInput.value = (trip.customPlaces || trip.selectedPlaces || []).join(", ");

  document.querySelectorAll("[name='interests']").forEach((checkbox) => {
    checkbox.checked = trip.interests.includes(checkbox.value);
  });

  document.querySelectorAll("[name='budgetStyle']").forEach((input) => {
    input.checked = input.value === (trip.budgetStyle || "Comfort");
  });

  document.querySelector("#planner").scrollIntoView({ behavior: "smooth" });
}

function duplicateTrip(trip) {
  const copy = {
    ...trip,
    id: crypto.randomUUID(),
    name: `${trip.name} Copy`,
    createdAt: new Date().toISOString()
  };
  saveTrip(copy);
}

function deleteTrip(tripId) {
  const key = storageKeys[state.listMode];
  setStoredTrips(
    key,
    getStoredTrips(key).filter((trip) => trip.id !== tripId)
  );
  updateCounts();
  renderTripList();
}

function updateCounts() {
  savedCount.textContent = getStoredTrips(storageKeys.saved).length;
  recentCount.textContent = getStoredTrips(storageKeys.recent).length;
}

function renderTripList() {
  const key = storageKeys[state.listMode];
  const trips = getStoredTrips(key);
  document.querySelector("#show-saved").className = state.listMode === "saved" ? "secondary-button" : "ghost-button";
  document.querySelector("#show-recent").className = state.listMode === "recent" ? "secondary-button" : "ghost-button";

  if (!trips.length) {
    tripList.innerHTML = `<div class="empty-result"><h3>No ${escapeHtml(
      state.listMode
    )} trips yet</h3><p>Generate an itinerary and save it to build your history.</p></div>`;
    return;
  }

  tripList.innerHTML = trips
    .map(
      (trip) => `
      <article class="trip-card">
        <h3>${escapeHtml(trip.name)}</h3>
        <p class="trip-meta">${escapeHtml(trip.destination)} • ${trip.days} days • ${formatMoney(
        trip.budget,
        trip.currency
      )}</p>
        <div class="trip-actions">
          <button type="button" data-trip-action="view" data-id="${trip.id}">View</button>
          <button type="button" data-trip-action="rename" data-id="${trip.id}">Rename</button>
          <button type="button" data-trip-action="duplicate" data-id="${trip.id}">Duplicate</button>
          <button type="button" data-trip-action="delete" data-id="${trip.id}">Delete</button>
        </div>
      </article>`
    )
    .join("");

  tripList.querySelectorAll("[data-trip-action]").forEach((button) => {
    button.addEventListener("click", () => {
      const trip = trips.find((item) => item.id === button.dataset.id);
      if (!trip) return;
      if (button.dataset.tripAction === "view") {
        state.currentTrip = trip;
        renderResult(trip);
        resultSection.scrollIntoView({ behavior: "smooth" });
      }
      if (button.dataset.tripAction === "rename") renameTrip(trip);
      if (button.dataset.tripAction === "duplicate") duplicateTrip(trip);
      if (button.dataset.tripAction === "delete") deleteTrip(trip.id);
    });
  });
}

function openAuth(tab) {
  switchAuthTab(tab);
  document.querySelector("#auth-dialog").showModal();
}

function closeAuthDialog() {
  document.querySelector("#auth-dialog").close();
}

function startGoogleAuth() {
  window.location.href = "/auth/google";
}

function emailAuthUnavailable() {
  showToast("Email login is not enabled yet. Use Google OAuth to continue.");
}

async function refreshSession(showSuccess = false) {
  try {
    const response = await fetch("/api/session", { credentials: "same-origin" });
    const session = await response.json();
    state.isLoggedIn = Boolean(session.authenticated);
    state.user = session.user || null;
    applyAuthState();
    if (state.isLoggedIn && showSuccess) {
      showToast(`Welcome, ${state.user.fullName}. Google authentication completed.`);
    }
  } catch {
    state.isLoggedIn = false;
    state.user = null;
    applyAuthState();
    showToast("Could not verify your session. Please try signing in again.");
  }
}

async function logoutUser() {
  try {
    await fetch("/auth/logout", {
      method: "POST",
      credentials: "same-origin"
    });
  } catch {
    showToast("Logout could not reach the server, but this browser view was locked.");
  }
  state.isLoggedIn = false;
  state.user = null;
  applyAuthState();
  showToast("Logged out. Planner and saved trips are hidden.");
  document.querySelector("#home").scrollIntoView({ behavior: "smooth" });
}

function switchAuthTab(tab) {
  document.querySelectorAll(".auth-tab").forEach((button) => {
    button.classList.toggle("active", button.dataset.authTab === tab);
  });
  document.querySelector("#login-pane").classList.toggle("active", tab === "login");
  document.querySelector("#register-pane").classList.toggle("active", tab === "register");
}

function applyAuthState() {
  document.body.classList.toggle("logged-in", state.isLoggedIn);
  document.body.classList.toggle("logged-out", !state.isLoggedIn);
}

function showAuthRedirectMessage() {
  const params = new URLSearchParams(window.location.search);
  const error = params.get("auth_error");
  const success = params.get("auth") === "success";
  const messages = {
    missing_google_config:
      "Google OAuth is not configured yet. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET on the server.",
    google_cancelled: "Google sign-in was cancelled. No account was created and no session was started.",
    invalid_oauth_state: "Google sign-in could not be verified. Please try again.",
    google_auth_failed: "Google authentication failed. No session was created."
  };

  if (error) {
    showToast(messages[error] || "Google authentication failed. Please try again.");
    window.history.replaceState({}, "", window.location.pathname + window.location.hash);
  }

  if (success) {
    refreshSession(true);
    window.history.replaceState({}, "", window.location.pathname + window.location.hash);
  }
}

function updateAdminStats() {
  const destinations = Object.values(destinationData);
  adminDestinations.textContent = destinations.length;
  adminAttractions.textContent = destinations.reduce((sum, destination) => sum + destination.attractions.length, 0);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => {
    const entities = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;"
    };
    return entities[character];
  });
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("active");
  clearTimeout(showToast.timeout);
  showToast.timeout = setTimeout(() => toast.classList.remove("active"), 2600);
}

init();
