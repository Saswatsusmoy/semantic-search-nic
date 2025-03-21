import difflib
import string, re
from functools import lru_cache
from spellchecker import SpellChecker
import time

spell = SpellChecker()

lis = []
with open("Data Processing/lemmatized_words.txt", 'r') as file:
    text = file.read()
    word_list = text.split()
    lis.extend(word_list)

def is_valid(word):
    return word in spell

def correct_words(text, word_list = lis, cutoff=0.7):
    words = text.split()
    corrected_text = []
    word_list_tuple = tuple(word_list)
    @lru_cache(maxsize=2048)
    def get_best_match(word):
        close_matches = difflib.get_close_matches(word, word_list_tuple, n=1, cutoff=cutoff)
        return close_matches[0] if close_matches else word
    for word in words:
        if is_valid(word):
            corrected_text.append(word)
        else:
            corrected_text.append(get_best_match(word))
    return " ".join(corrected_text)


test_list = [
    "hedphones", "on", "quality", "vedors", "kamelids", "evaporation", "inkubators", "rezinoids", 
    "schooll", "estate", "meical", "ballast", "strin", "cicuits", "remote", "zillimanite", "mock", 
    "clmps", "vanadium", "advertisements", "biders", "intruction", "drving", "car", "goodz", "related", 
    "rollss", "ezters", "entail", "printingg", "day", "applicant", "room", "flazh", "animals", "zhredding", 
    "washbasins", "iradiation", "unifferenciated", "cocoa", "leveller", "store", "modified", "reerve", 
    "evaluation", "kultured", "condense", "sesoned", "offshore", "guides", "grinding", "burnin", 
    "disinfectantss", "vaultz", "alarm", "line", "collectin", "affairz", "care", "directorie", 
    "secondaryy", "tapestry", "transmissionn", "inlatable", "ambulanke", "azsociated", "gining", 
    "convalescentt", "fuch", "r", "gemztones", "perennial", "veneer", "blastingg", "assistancee", 
    "melonss", "hume", "bath", "breakin", "shampoos", "anennas", "zchedule", "teples", "unmarriedd", 
    "industry", "buyer", "wet", "designin", "zettlement", "moorcycle", "maches", "fermented", 
    "moorcycles", "prjectors", "shockk", "petrol", "grinders", "caturing", "snack", "multiple", 
    "brquettes", "searchabl", "lease", "hewn", "industries", "fixtures", "threade", "union", "unts", 
    "flushingg", "prpared", "apparatu", "preciou", "dokument", "mozses", "preservation", "leels", 
    "sculptor", "fariers", "pome", "easily", "mortgagez", "conveyo", "persona", "ozokerite", "portz", 
    "depositor", "gladioluss", "misiles", "non", "pulleyz", "providerz", "contractt", "clock", 
    "bailingg", "retoring", "pulsess", "projectss", "cocentrates", "protein", "roll", "statuette", 
    "assemblyy", "soup", "associationss", "indoor", "sefood", "heaters", "wells", "klaims", "concerne", 
    "rollingg", "religiou", "paint", "sealin", "aaya", "steatitee", "agencyy", "monitoring", "bodyguard", 
    "clien", "arrangingg", "turpentine", "blended", "departmentt", "garnetted", "player", "pets", "opec", 
    "economicc", "acetylsalicyli", "trains", "aqatic", "milking", "trsses", "eliminatee", "ocupational", 
    "collectionn", "calcine", "cordagee", "skion", "operato", "term", "deined", "apliances", "herbicide", 
    "beds", "canal", "tiling", "crude", "refrigeratedd", "califlower", "railway", "manikure", "tanningg", 
    "kollective", "poliky", "ranching", "lawn", "plumbing", "clssification", "pots", "titing", "elewhere", 
    "lens", "sport", "geodeti", "clientelee", "trck", "based", "ekonomists", "dealingg", "fiers", 
    "radiator", "managingg", "nibium", "die", "partition", "lihthouse", "carbonate", "cheque", "manetic", 
    "central", "glazess", "dokumentation", "integrated", "ore", "coachess", "purkhsed", "dekision", 
    "ropess", "granting", "occupiedd", "cosulting", "internall", "not", "chutne", "bringin", "dairy", 
    "takerss", "separators", "involve", "faming", "clad", "ringz", "telecommunication", "card", 
    "broomss", "chemically", "ballast", "remova", "grmophone", "mothers", "guava", "threshingg", "skiffs", 
    "cake", "citru", "carry", "exteriors", "searc", "cucumberz", "forestss", "higher", "pigs", "vicess", 
    "connectorss", "immediat", "geneticallyy", "faciall", "tractorss", "markerr", "guns", "packagedd", 
    "beeswa", "gluez", "live", "rokwool", "dying", "plywood", "cycle", "aviatio", "uzable", "tuors", 
    "pipelines", "gathering", "safe", "swtchgear", "deigners", "prpare", "kanned", "examiners", "factory", 
    "selenit", "amplifierz", "platingg", "ups", "exploitationn", "aimed", "cleaverz", "savingss", "konsumers", 
    "electr", "potas", "hotels", "anse", "more", "ticket", "hosieryy", "belowground", "zubsistence", 
    "annuall", "ground", "plastic", "wax", "printe", "free", "pont", "hodalls", "treatmentt", "electrica", 
    "naturall", "konferences", "fighting", "nurse", "turbojetz", "bins", "mail", "chezts", "bots", "taped", 
    "krushers", "blockss", "bazis", "file", "india", "diisions", "intructional", "terminal", "zprouting", 
    "vesels", "relatingg", "loaderss", "turnipz", "rubby", "fluid", "flating", "inztructions", "diesel", "crating"
]


test_out = [
    "headphones", "on", "quality", "vendors", "camelids", "evaporation", "incubators", "resinoids", 
    "school", "estate", "medical", "ballasts", "string", "circuits", "remote", "sillimanite", 
    "mock", "clamps", "vanadium", "advertisements", "binders", "instruction", "driving", "car", 
    "goods", "related", "rolls", "esters", "entail", "printing", "day", "applicants", "room", 
    "flash", "animals", "shredding", "washbasins", "irradiation", "undifferenciated", "cocoa", 
    "levellers", "store", "modified", "reserve", "evaluation", "cultured", "condensed", "seasoned", 
    "offshore", "guides", "grinding", "burning", "disinfectants", "vaults", "alarm", "line", 
    "collecting", "affairs", "care", "directories", "secondary", "tapestry", "transmission", 
    "inflatable", "ambulance", "associated", "ginning", "convalescent", "fuch", "r", "gemstones", 
    "perennial", "veneer", "blasting", "assistance", "melons", "hume", "bath", "breaking", "shampoos", 
    "antennas", "schedule", "temples", "unmarried", "industry", "buyer", "wet", "designing", 
    "settlement", "motorcycle", "matches", "fermented", "motorcycles", "projectors", "shock", 
    "petrol", "grinders", "capturing", "snacks", "multiple", "briquettes", "searchable", "leased", 
    "hewn", "industries", "fixtures", "threaded", "union", "units", "flushing", "prepared", "apparatus", 
    "precious", "document", "mosses", "preservation", "levels", "sculptors", "farriers", "pome", "easily", 
    "mortgages", "conveyor", "personal", "ozokerite", "ports", "depository", "gladiolus", "missiles", 
    "non", "pulleys", "providers", "contract", "clocks", "bailing", "restoring", "pulses", "projects", 
    "concentrates", "protein", "roll", "statuettes", "assembly", "soup", "associations", "indoor", 
    "seafood", "heaters", "wells", "claims", "concerned", "rolling", "religious", "paint", "sealing", 
    "aaya", "steatite", "agency", "monitoring", "bodyguard", "client", "arranging", "turpentine", 
    "blended", "department", "garnetted", "players", "pets", "opec", "economic", "acetylsalicylic", 
    "trains", "aquatic", "milking", "trusses", "eliminate", "occupational", "collection", "calcined", 
    "cordage", "scion", "operator", "term", "defined", "appliances", "herbicides", "beds", "canal", 
    "tiling", "crude", "refrigerated", "cauliflower", "railway", "manicure", "tanning", "collective", 
    "policy", "ranching", "lawn", "plumbing", "classification", "pots", "tinting", "elsewhere", "lens", 
    "sport", "geodetic", "clientele", "track", "based", "economists", "dealing", "fibers", "radiators", 
    "managing", "niobium", "die", "partition", "lighthouse", "carbonate", "cheque", "magnetic", "central", 
    "glazes", "documentation", "integrated", "ore", "coaches", "purchsed", "decision", "ropes", "granting", 
    "occupied", "consulting", "internal", "not", "chutney", "bringing", "dairy", "takers", "separators", 
    "involve", "farming", "clad", "rings", "telecommunication", "card", "brooms", "chemically", "ballast", 
    "removal", "gramophone", "mothers", "guava", "threshing", "skiffs", "cake", "citrus", "carry", "exteriors", 
    "search", "cucumbers", "forests", "higher", "pigs", "vices", "connectors", "immediate", "genetically", 
    "facial", "tractors", "marker", "guns", "packaged", "beeswax", "glues", "live", "rockwool", "dying", 
    "plywood", "cycles", "aviation", "usable", "tutors", "pipelines", "gathering", "safe", "switchgear", 
    "designers", "prepare", "canned", "examiners", "factory", "selenite", "amplifiers", "plating", "ups", 
    "exploitation", "aimed", "cleavers", "savings", "consumers", "electro", "potash", "hotels", "anise", 
    "more", "tickets", "hosiery", "belowground", "subsistence", "annual", "ground", "plastics", "wax", 
    "printed", "free", "point", "holdalls", "treatment", "electrical", "natural", "conferences", "fighting", 
    "nurses", "turbojets", "bins", "mail", "chests", "bolts", "taped", "crushers", "blocks", "basis", "file", 
    "india", "divisions", "instructional", "terminal", "sprouting", "vessels", "relating", "loaders", "turnips", 
    "rubby", "fluid", "floating", "instructions", "diesel", "crating"
]

cou_r = 0
cou_w = 0
cou_un = 0
tot = 0 

def clean_sentence(input_string):
    input_string = input_string.replace("-", " ").replace("–", " ").replace("—", " ").replace(':', ' ').replace("।", "")
    if not isinstance(input_string, str):
        return ""    
    remove_chars = string.punctuation + '|'
    for char in remove_chars:
        input_string = input_string.replace(char, "")
    result = input_string.strip().lower()
    result = re.sub(r'\s+', ' ', result)
    return result

start = time.time()
for i in range(len(test_list)):
    wrong = test_list[i]
    corrected = correct_words(clean_sentence(wrong), word_list)
    if clean_sentence(corrected) == clean_sentence(test_out[i]):
        cou_r = cou_r + 1
    elif clean_sentence(corrected[:-1]) == clean_sentence(test_out[i]) or clean_sentence(corrected) == clean_sentence(test_out[i][:-1]):
        cou_r = cou_r + 1
    elif clean_sentence(corrected) == clean_sentence(wrong):
        cou_un = cou_un + 1        
    else:
        cou_w = cou_w + 1
        print("Wrong: ", wrong, "Corrected: ", corrected, "Expected: ", test_out[i])
    tot = tot+1
end = time.time()

print(f"Correct: {cou_r} Wrong: {cou_w} Untouched: {cou_un} Total: {tot}")
print("Accuracy:", cou_r/(tot-cou_un)*100)
print(f"Time taken: {end-start}")
