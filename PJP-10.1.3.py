#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified PAQJP+PJP — Dual Method + 12 Downloads + Real Dictionary
================================================================
Method A → input.pjp2 : 256 transforms + PAQ/Zstd/Brotli (raw)
Method B → input.pjp3 : 256 transforms + LZH + SHA-256 (PJP4 magic)

Option 1 tries BOTH, keeps SMALLER, deletes the other.
Decompression auto-detects format.

★ 100% LOSSLESS ★
★ zstandard MANDATORY — will retry import after every install attempt ★

Word batches:
  • A through L are embedded below (A, B, C, D, E, F, G, J, K, L).
  • H and I are loaded from ./word_batches/batch_H.txt / batch_I.txt (skipped if absent).
"""

import math, random, decimal, hashlib, base64, heapq, struct, os, tempfile
import re, sys, subprocess, importlib, time, urllib.request, site
from typing import Optional, List, Tuple, Dict, Callable, Any
from collections import Counter

# ============================ BACKENDS ============================
try: import paq
except ImportError: paq = None
try:
    import brotli; HAS_BROTLI = True
except ImportError:
    brotli = None; HAS_BROTLI = False

USE_QUANTUM = False
HAS_QISKIT = False
HAS_ZSTD = False

# ==================================================================
# ★ BULLET-PROOF ZSTANDARD INSTALLER ★
# ==================================================================
def _try_import_zstd():
    try:
        importlib.invalidate_caches()
        user_site = site.getusersitepackages()
        if user_site and user_site not in sys.path:
            sys.path.insert(0, user_site)
    except Exception:
        pass
    try:
        import zstandard as zstd
        return zstd
    except ImportError:
        return None

def _try_install_zstd():
    cmds = [
        [sys.executable, '-m', 'pip', 'install', '--no-input', '--disable-pip-version-check', 'zstandard'],
        [sys.executable, '-m', 'pip', 'install', '--user', '--no-input', '--disable-pip-version-check', 'zstandard'],
        [sys.executable, '-m', 'pip', 'install', '--break-system-packages', '--no-input', '--disable-pip-version-check', 'zstandard'],
        ['pip', 'install', '--no-input', '--disable-pip-version-check', 'zstandard'],
        ['pip3', 'install', '--no-input', '--disable-pip-version-check', 'zstandard'],
    ]
    for cmd in cmds:
        print(f"  Trying: {' '.join(cmd)}")
        try:
            subprocess.check_call(cmd)
            print(f"  OK command succeeded, retrying import...")
            if _try_import_zstd() is not None:
                print(f"  SUCCESS!")
                return True
        except Exception as e:
            print(f"  FAILED: {e}")
    return False

print("=" * 70)
print("Checking zstandard (MANDATORY backend)...")
print("=" * 70)

_zstd = _try_import_zstd()

if _zstd is None:
    print("zstandard NOT FOUND. Trying to install automatically...")
    if not _try_install_zstd():
        print()
        print("=" * 70)
        print("FATAL: Could not install zstandard automatically.")
        print()
        print("Please open a TERMINAL and run one of these commands:")
        print()
        print("    pip install zstandard")
        print("    pip install --user zstandard")
        print("    pip install --break-system-packages zstandard")
        print()
        print("Then re-run this script.")
        print("=" * 70)
        sys.exit(1)
    _zstd = _try_import_zstd()
    if _zstd is None:
        print("FATAL: zstandard installed but still cannot be imported.")
        print("Try closing and reopening the Python process / Codespace.")
        sys.exit(1)

zstd = _zstd
zstd_cctx = zstd.ZstdCompressor(level=22)
zstd_dctx = zstd.ZstdDecompressor()
HAS_ZSTD = True
print("zstandard loaded successfully.")

# ==================================================================
# Optional backends
# ==================================================================
def install_package(pkg):
    print(f"Installing {pkg}...")
    for cmd in [
        [sys.executable, '-m', 'pip', 'install', '--no-input', '--disable-pip-version-check', pkg],
        [sys.executable, '-m', 'pip', 'install', '--user', '--no-input', '--disable-pip-version-check', pkg],
        ['pip', 'install', '--no-input', '--disable-pip-version-check', pkg],
    ]:
        try: subprocess.check_call(cmd); print(f"  OK {pkg}"); return True
        except Exception as e: print(f"  FAIL: {e}")
    return False

if input("Option 1: Quantum (Qiskit)? (y/n) [n]: ").strip().lower() == 'y':
    try:
        from qiskit import QuantumCircuit
        HAS_QISKIT = True; USE_QUANTUM = True; print("Quantum ENABLED.")
    except ImportError:
        if install_package('qiskit'):
            try:
                from qiskit import QuantumCircuit
                HAS_QISKIT = True; USE_QUANTUM = True; print("Quantum ENABLED.")
            except ImportError: print("Qiskit failed.")
        else: print("Qiskit failed.")
else: print("Quantum disabled.")

if input("Option 2: Install paq + brotli? (y/n) [y]: ").strip().lower() != 'n':
    for pkg in ['paq', 'brotli']:
        try: importlib.import_module(pkg); print(f"{pkg} present.")
        except ImportError: install_package(pkg)
    try: import paq
    except ImportError: paq = None
    try: import brotli; HAS_BROTLI = True
    except ImportError: brotli = None; HAS_BROTLI = False
else: print("Skipping paq + brotli.")

print(f"\nBackends: zstd=Y paq={'Y' if paq else 'N'} brotli={'Y' if HAS_BROTLI else 'N'}")

PROGNAME = "UnifiedPAQJP+PJP (Dual-Method + 12 Downloads + Real Dict)"

# ============================ DICTIONARY ============================
DICT_DIR = "Dictionaries"
COMBINED_DICTIONARY_FILE = os.path.join(DICT_DIR, "dictionary_combined.txt")
MAX_LINE_ENTRIES = 1024

DICTIONARY_FILES = [
    "generated.txt", "eng_news_2005_1M-sentences.txt", "eng_news_2005_1M-words.txt",
    "eng_news_2005_1M-sources.txt", "eng_news_2005_1M-co_n.txt", "eng_news_2005_1M-co_s.txt",
    "eng_news_2005_1M-inv_w_2.txt", "eng_news_2005_1M-inv_w_3.txt", "eng_news_2005_1M-inv_so.txt",
    "eng_news_2005_1M-meta.txt", "Dictionary.txt",
    "the-complete-reference-html-css-fifth-edition.txt",
]
DICTIONARY_URLS = [
    "https://drive.google.com/uc?export=download&id=1u_1dCEl8hhdEug6GwkOxHAu_rawSx_6_Pme9",
    "https://drive.google.com/uc?export=download&id=1pVqNN5JZ2AeOCgRaHkv4Vv6Byr4zK20e",
    "https://drive.google.com/uc?export=download&id=1ZSC-Tn76x8itdN0rCp-Zw17hGudxbjxo",
    "https://drive.google.com/uc?export=download&id=1VB_7tzngs4GxjclSRyRDnxgS8znT2w2S",
    "https://drive.google.com/uc?export=download&id=1KVIRgiMrhCUCqQZJ3UT67ztls2GqGJzz",
    "https://drive.google.com/uc?export=download&id=1Z3Lx6SqL4HWsnmbJCez4kXWRQQhUXWKL",
    "https://drive.google.com/uc?export=download&id=1br2bdRMkZEVVRPKYmC4IIaZuAjxFJE4N",
    "https://drive.google.com/uc?export=download&id=1aE6ubPZiJ8rr3lEVk8fFJYjDQ1y1rU0X",
    "https://drive.google.com/uc?export=download&id=1uro3TZe-t5zPx2Qu2xrTL3lU8N0melk9",
    "https://drive.google.com/uc?export=download&id=1HqsTH1DqpWNpGbn9VtD7-SB6wVqA90R2",
    "https://drive.google.com/uc?export=download&id=1zZ8iMeBC3605NZhuc4UE9jx_w_lZFg5B",
    "https://drive.google.com/uc?export=download&id=1dDdqYDgm7f-smS7KF70Wf0KmyFo-ft1M",
]

# ==================================================================
# ★ REAL WORDS — EMBEDDED BATCHES A & B
# ==================================================================
REAL_WORDS_5000 = """
able about above abroad absence absent absolute absorb abstract abuse accent accept access accident
accompany accomplish accord account accurate accuse achieve acid acknowledge acquire across act action
active activity actor actress actual adapt add addition address adequate adjust administration admire
admit adopt adult advance advantage adventure advertise advice advise affair affect afford afraid
africa after afternoon again against age agency agenda agent aggressive ago agree agriculture ahead
aid aim air aircraft airline airport alarm album alcohol alive all alliance allow almost alone along
already also alter alternative although always amateur amazing among amount analysis analyst ancient
and anger angle angry animal anniversary announce annual another answer anxiety any anybody anymore
anyone anything anyway anywhere apart apartment apologize apparent appeal appear apple application
apply appoint appreciate approach appropriate approve april architecture area argue argument arise arm
army around arrange arrest arrival arrive arrow art article artist as ashamed asia aside ask asleep
aspect assault assert assess asset assign assist associate assume assure asteroid astonish athlete
atlantic atmosphere atom attach attack attempt attend attention attitude attorney attract auction
audience august aunt author authority auto autumn available average avoid awake award aware away
awful baby back background backup bacon bad badly bag bake balance ball balloon ban banana band bank
bar barely bargain barrel barrier base baseball basic basis basket basketball bath bathroom battery
battle bay beach bean bear beard beast beat beautiful beauty because become bed bedroom bee beef beer
before beg begin beginning behalf behave behavior behind being belief believe bell belong below belt
bench bend beneath benefit beside besides best bet better between beyond bicycle bid big bike bill
billion bind biology bird birth birthday biscuit bit bite bitter black blade blame blank blanket
blast bleed blend bless blind block blood bloom blow blue board boat body boil bold bomb bond bone
bonus book boom boost boot border bore boring born borrow boss both bother bottle bottom bounce bound
boundary bow bowl box boy brain branch brand brass brave bread break breakfast breast breath breathe
breed brick bridge brief bright brilliant bring broad broken bronze brook brother brown brush bubble
bucket budget buffalo bug build building bulb bulk bullet bunch bundle burden bureau burn burst bury
bus bush business busy but butter butterfly button buy cabin cable cage cake calculate calendar call
calm camera camp campaign campus can canal cancel cancer candidate candle candy cannon canoe canvas
cap capable capacity cape capital captain capture carbon card care career careful cargo carpet carry
cart cartoon carve case cash cast castle casual cat catalog catch category cattle cause caution cave
cease ceiling celebrate cell cellar cement cemetery census cent center central century cereal ceremony
certain certificate chain chair chairman chalk challenge chamber champion chance change channel chaos
chapter character charge charity charm chart charter chase cheap cheat check cheek cheer cheese chef
chemical cherry chess chest chew chicken chief child childhood chill chimney chin china chip chocolate
choice choose chop chorus christian christmas church cigarette cinema circle circuit circumstance cite
citizen city civil claim clap clarify clash class classic clause clay clean clear clergy clerk clever
click client cliff climate climb clinic clip clock close closet cloth clothes cloud club clue cluster
coach coal coast coat code coffee coin cold collapse collar colleague collect college colonial column
combine come comedy comfort comic command comment commerce commission commit committee common
communicate community company compare compete complain complete complex comply component compose
compound comprehensive compromise computer conceal concede conceive concentrate concept concern concert
conclude concrete condition conduct conference confess confidence confirm conflict confront confuse
congress connect conscious consent consider consist console constant constitute constrain construct
consult consume contact contain contemporary contempt contend content contest context continent continue
contract contrast contribute control controversy convenient convention conversation convert convey
convict convince cook cool cooperate cope copy copper core corn corner corporate correct corridor cost
cottage cotton couch cough could council counsel count counter country county couple courage course
court cousin cover cow crack craft crash crazy cream create creature credit creek crew cricket crime
criminal crisis crisp critic critical crop cross crowd crown crucial crude cruel cruise crush cry
crystal cube cuisine cultural culture cup cupboard cure curious currency current curriculum curtain
curve cushion custom customer cut cycle daily dairy dam damage damp dance danger dare dark darling dash
data database date daughter dawn day dead deadline deaf deal dear death debate debt decade decent
decide decision deck declare decline decorate decrease dedicate deed deep deer defeat defend define
definite degree delay delegate delicate delicious delight deliver demand democracy demonstrate deny
depart department depend deposit depress depth deputy derive describe desert deserve design desire
desk desperate despite dessert destroy detail detect determine develop device devote diagram dial
diamond diary dictionary die diet differ difficult dig digital dignity dilemma dinner dip diplomatic
direct dirt dirty disagree disappear disaster discipline disclose discount discover discuss disease
disguise disgust dish dismiss disorder display dispose dispute distance distinct distribute district
disturb ditch dive diverse divide divorce dizzy dock doctor doctrine document dodge dog doll dollar
domain domestic dominant donate donkey donor door dose double doubt dough dove down downstairs downtown
dozen draft drag drain drama dramatic draw drawer dream dress drift drill drink drive driver drop drought
drown drug drum drunk dry duck due dull dump during dust duty dwarf dye dynamic each eager eagle early
earn earth ease east easy eat echo economy edge edit educate effect efficient effort egg eight either
elbow elder elect electric elegant element elephant elevator eleven eliminate elite else elsewhere
email embarrass embrace emerge emergency emotion emperor emphasis empire employ empty enable enclose
encounter encourage end endless endorse enemy energy enforce engage engine engineer enhance enjoy
enormous enough ensure enter entertain enthusiasm entire entitle entrance entry envelope environment
envy episode equal equip era error escape especially essay essence essential establish estate estimate
eternal ethic ethnic evaluate even evening event eventually ever every everybody everyday everyone
everything everywhere evidence evil exact examine example exceed excellent except exchange excite
exclude excuse execute exercise exhaust exhibit exile exist exit expand expect expense experience
experiment expert explain explode exploit explore export expose express extend extent external extra
extraordinary extreme eye fabric face facility fact factor factory fade fail faint fair faith fall
false fame family famous fan fancy fantasy far farm fashion fast fat fatal fate father fault favor
favorite fear feast feather feature federal fee feed feel fellow female fence ferry festival fetch
fever few fiber fiction field fierce fifteen fifty fight figure file fill film filter final finance
find fine finger finish fire firm first fish fist fit five fix flag flame flash flat flavor flee flesh
flight float flood floor flour flow flower flu fluid flush fly foam focus fog fold folk follow fond
food fool foot football force forecast foreign forest forever forgive fork form formal format former
formula fort fortune forum forward foster found foundation fountain four fraction frame framework
france frank fraud free freedom freeze french frequent fresh friend friendly fright frog from front
frost frown frozen fruit fuel full fun function fund funeral funny fur furnace furniture further
future gain galaxy gallery gallon gamble game gang gap garage garbage garden garlic gas gate gather
gauge gaze gear gender gene general generate generous genius gentle gentleman genuine geography germ
german gesture get ghost giant gift gigantic girl give glad glance glare glass gleam glide glimpse
global globe gloom glory glove glow glue goal goat god gold golf good goodbye goods gorgeous gospel
gossip govern gown grab grace grade gradual graduate grain grand grandfather grandmother grant grape
graph grasp grass grateful grave gravity gray grease great greed green greet grid grief grin grind
grip grocery gross ground group grow growth guarantee guard guess guest guidance guide guilt guilty
guitar gulf gun gym habit habitat hair half hall halt hammer hand handful handle handsome hang happen
happy harbor hard hardly hardware harm harmony harsh harvest haste hat hate haul have hawk hay hazard
haze head headline health heap hear heart heat heaven heavy heel height helicopter hell hello helmet
help hence herb herd here heritage hero herself hesitate hidden hide high highlight highway hill him
himself hint hip hire historic history hit hobby hold hole holiday hollow holy home honest honey honor
hook hope horizon horn horrible horror horse hospital host hostile hot hotel hour house household
housing however hug huge human humble humor hundred hunger hungry hunt hurry hurt husband hut hybrid
hydrogen hymn ice icon idea ideal identity idle idol ignore ill illegal illness illusion image imagine
imitate immediate immense immigrant immune impact imperial implement imply import impose impress
improve impulse inch include income increase incredible indeed independence index indicate individual
indoor induce industrial industry infant infect infer infinite inflation influence inform ingredient
inhabit inherit initial initiate inject injure ink inn inner innocent innovation input inquiry
insect insert inside insight insist inspect inspire install instance instant instead instinct
institute instruct instrument insult insurance intact integrate intellectual intelligence intend
intense intention interact interest interfere interior internal internet interpret interrupt
interval intervene interview intimate introduce invade invent invest investigate invite involve iron
ironic irony island isolate issue item ivory jacket jail jam january japan jar jaw jazz jealous jeans
jet jewel job join joint joke journal journey joy judge judgment juice july jump june jungle junior
junk jury just justice justify keen keep kernel kettle key keyboard kick kid kidnap kidney kill kilo
kind kindle king kingdom kiss kitchen kite knee kneel knife knight knit knob knock knot know knowledge
lab label labor laboratory lace lack ladder lady lag lake lamb lamp land landscape lane language lap
large laser last late laugh launch laundry law lawn lawyer lay layer lazy lead leader leaf league leak
lean leap learn lease least leather leave lecture left leg legal legend legislation legitimate leisure
lemon lend length lens leopard less lesson let letter level liability liberal liberty library license
lid lie life lift light like likely limb limit line link lion lip liquid list listen literally literary
literature litter little live liver load loan lobby local locate lock logic lonely long look loop loose
lord lose loss lost lot loud love low loyal loyalty luck lucky luggage lump lunar lunch lung luxury
machine mad magic magnet mail main maintain major make male mall manage manner manual manufacture many
map marble march margin marine mark market marriage marry marsh mask mass massive master match mate
material math matter mature maximum maybe mayor meadow meal mean meaning measure meat mechanic medal
media medical medicine medium meet melody melon melt member memory mention menu mercy mere merge merit
merry mess message metal meter method middle midnight might mild mile military milk mill million mind
mine mineral minimum minister minor mint minute miracle mirror miss missile mission mist mistake mix
mixture mobile mode model moderate modern modest modify moist moment money monitor monkey month mood
moon moral more morning mortgage most mother motion motive motor mount mountain mourn mouse mouth move
movie much mud mug multiple murder muscle museum mushroom music musician must mutual myself mystery
myth nail naked name nap narrow nation native natural nature naughty navy near neat necessary neck
need needle negative neglect negotiate neighbor neither nephew nerve nest net network neutral never
nevertheless new news next nice niece night nine noble nobody nod noise nominal none noon nor normal
north nose not note nothing notice notion noun novel november now nowhere nuclear number nurse nut
object objective obligation observe obtain obvious occasion occupy occur ocean october odd odor off
offend offer office official often oil okay old olive omit once one onion online only onto open opera
operate opinion opponent opportunity oppose opposite option orange orbit orchard order ordinary organ
organic organize origin ornament orphan other otherwise ought ounce our ours ourselves out outcome
outdoor outer outfit outline output outside oven over overall overcome overlap overlook owe owl own
owner oxygen pace pack package pact pad page pain paint pair palace pale palm pan panel panic paper
parade paragraph parallel parcel pardon parent park parliament part partial participate particle
particular partner party pass passage passenger passion passive past pasta paste pastry patch path
patience patient pattern pause pave payment peace peak peanut pear pearl peasant peculiar pedal peel
peer pen penalty pencil pendulum penetrate penguin peninsula pension people pepper per percent perfect
perform perhaps period permit person personal personality persuade pest pet phase phenomenon philosophy
phone photo phrase physical piano pick picnic picture pie piece pig pigeon pile pill pillow pilot pin
pine pink pioneer pipe pistol pit pitch pity pizza place plain plan plane planet plant plastic plate
platform play pleasant please pleasure plenty plot plug plunge plus pocket poem poet poetry point
poison polar pole police policy polish polite political politics poll pollution pond pool poor pop
popular population porch port portion portrait portray pose position positive possess possible post
pot potato potential pound pour poverty powder power practice praise pray prayer preach precise predict
prefer pregnant preliminary premise premium preparation prepare prescribe presence present preserve
preside press pressure pretend pretty prevail prevent previous prey price pride priest primary prime
prince princess principal principle print prior priority prison privacy private privilege prize
probable problem proceed process proclaim produce product profession professor profile profit profound
program progress prohibit project prominent promise promote prompt proof proper property prophet
proportion proposal propose prospect protect protein protest proud prove provide province provoke
psychology public publish pull pump punch punish pupil purchase pure purpose purse pursue push put
puzzle pyramid quality quantity quarrel quarter queen quest question queue quick quiet quit quite
quote rabbit race radar radiation radical radio radius rage rail railway rain rainbow raise rally
random range rank rapid rare rat rate rather ratio rational raw ray razor reach react read ready real
reality realize realm rear reason rebel recall receipt receive recent reception recipe recognize
recommend record recover recruit reduce refer reflect reform refuse regard regime region register
regret regular regulate reject relate relative relax release relevant reliable relief religion
reluctant rely remain remark remedy remember remind remote remove render renew rent repair repeat
replace reply report represent republic reputation request require rescue research resemble reserve
reside resign resist resolve resort resource respect respond response responsibility rest restaurant
restore restrict result resume retail retain retire retreat return reveal revenue reverse review
revise revolution reward rhythm rib ribbon rice rich rid ride ridge ridiculous rifle right rigid ring
riot rise risk ritual rival river road roast rob robot rock rocket rod role roll roman romantic roof
room root rope rose rotate rough round route routine row royal rub rubber rude rug ruin rule rumor
run rural rush sacred sacrifice sad saddle safe sail saint sake salad salary sale salmon salt same
sample sand sandwich satellite satisfy sauce sausage save saving say scale scan scandal scare scatter
scene schedule scheme scholar school science scientific scientist scope score scorn scout scrap scream
screen screw script scroll sculpture sea seal search season seat second secret section sector secure
seed seek seem segment seize seldom select self sell semester seminar senate send senior sense
sensitive sentence separate september sequence series serious servant serve service session set settle
seven several severe sew shade shadow shake shall shallow shame shape share shark sharp shatter shave
sheep sheet shelf shell shelter shepherd shield shift shine ship shirt shock shoe shoot shop shore
short shot shoulder shout shove show shower shrimp shrink shrug shut shy sibling sick side siege sigh
sight sign signal significant silence silent silk silly silver similar simple sin since sincere sing
single sink sir sister sit site situation six size skate sketch ski skill skin skip skirt skull sky
slave sleep sleeve slice slide slight slim slip slope slot slow small smart smash smell smile smoke
smooth snake snap sneak snow soap social society sock soft software soil solar soldier sole solid
solve some somebody somehow someone something sometime sometimes somewhat somewhere son song soon
sophisticated sore sorrow sorry sort soul sound soup sour source south space spare spark speak special
species specific specimen spectacle spectator speech speed spell spend sphere spice spider spill spin
spine spirit spit spite splash split spoil spoke sponge spoon sport spot spouse spray spread spring
sprout spy square squeeze stab stability stable stack stadium staff stage stair stake stale stall
stamp stance stand standard star stare start starve state statement station statue status stay steady
steak steal steam steel steep steer stem step stereo stick stiff still stimulate sting stir stock
stomach stone stool stop storage store storm story stove straight strain strand strange stranger
strap strategy straw stream street strength stress stretch strict strike string strip stripe stroke
stroll strong structure struggle stubborn student studio study stuff stumble stupid style subject
submit subscribe subsequent substance substitute subtle suburb succeed success such sudden sue suffer
sufficient sugar suggest suit suitable sulfur sum summer summit summon sun sunday sunny sunrise sunset
superior supermarket supper supply support suppose supreme sure surface surgery surplus surprise
surrender surround survey survival survive suspect suspend sustain swallow swan swap swear sweat sweep
sweet swell swift swim swing switch sword symbol sympathy symphony symptom syndrome system table
tablet tackle tactic tag tail tailor take tale talent talk tall tame tank tap tape target task taste
tax taxi tea teach team tear tease technical technique technology teeth telephone telescope television
tell temper temperature temple temporary tempt ten tend tendency tender tennis tense tent term terminal
terrible territory terror test testify testimony text than thank theater theme themselves then theory
therapy there therefore these they thick thief thin thing think third thirst thirteen thirty this
thorough those though thought thousand thread threat three thrive throat throne through throughout
throw thrust thumb thunder thus ticket tide tidy tie tiger tight tile till timber time tiny tip tire
tired tissue title toast tobacco today toe together toilet token tolerance tolerate toll tomato tomb
tomorrow ton tone tongue tonight too tool tooth top topic torch torn torture toss total touch tough
tour tourist tournament toward towel tower town toy trace track trade tradition traffic tragedy trail
train trait transfer transform transit translate transmit transport trap trash travel tray treasure
treat treaty tree tremble tremendous trend trial triangle tribe tribute trick trigger trim trip triumph
trivial troop trophy tropical trouble trousers truck true truly trunk trust truth try tube tunnel
turkey turn twelve twenty twice twin twist two type typical ugly ultimate umbrella unable uncertain
uncle under undergo underground understand undertake underwear undo unemployment unexpected unfair
unfold unhappy uniform union unique unit unite unity universal universe university unknown unless
unlike unlikely until unusual unveil upgrade uphold upstairs urban urge urgent us usage use useful
useless user usual utility utilize utter vacation vacuum vague valid valley valuable value van vanish
vanity vapor variable variety various vary vast vegetable vehicle veil vein velvet vendor venture
verb verdict verge verify verse version vertical very vessel veteran via vibrate vice victim victory
video view village vine vinegar violence violet violin virtue virus visa visible vision visit visual
vital vitamin vivid vocabulary voice void volcano volume volunteer vote voyage wage wagon waist wait
waiter wake walk wall wallet wander want war ward warehouse warm warn warning warrant warrior wash
waste watch water wave wax way weak wealth weapon wear weary weather weave web wedding wedge weed week
weekend weekly weep weigh weight weird welcome welfare well west wet whale what whatever wheat wheel
when whenever where whereas wherever whether which while whisper white who whole whom whose why wide
widow width wife wild will willing win wind window wine wing wink winner winter wipe wire wisdom wise
wish wit witch with withdraw within without witness wolf woman wonder wonderful wood wooden wool word
work worker world worm worry worse worship worst worth wound wrap wreck wrist write writer wrong yard
yell yellow yes yesterday yet yield yoga you young your yours yourself youth zero zone zoo
africa alabama alaska albania algeria amazon america amsterdam andorra angola antigua arabia arctic
argentina arizona armenia asia athens atlanta australia austria babylon baghdad bahamas bahrain
baltimore bangkok bangladesh barbados barcelona beijing beirut belarus belgium belgrade belize bengal
berlin bermuda bhutan bolivia bordeaux boston brazil brisbane britain brooklyn brussels bucharest
budapest buenos bulgaria burma cairo calcutta calgary california cambodia cameroon canada canberra
caracas caribbean carolina casablanca chicago chile china colombia colorado columbus congo copenhagen
croatia cuba cyprus czech dakota damascus delhi denmark detroit dublin ecuador edinburgh egypt
england estonia ethiopia europe fiji finland flanders florida france frankfurt gabon geneva georgia
germany ghana gibraltar greece greenland grenada guatemala guinea haiti hanoi harvard havana hawaii
helsinki holland honduras honolulu houston hungary iceland idaho illinois india indiana indonesia
iowa iran iraq ireland israel istanbul italy jamaica japan java jerusalem jordan jupiter kabul
kansas kashmir kazakhstan kentucky kenya khartoum korea kuwait kyoto laos latvia lebanon liberia
libya london louisiana luxembourg madagascar madrid maine malaysia maldives mali malta manchester
manila manitoba morocco moscow montana montreal morocco mumbai munich nagoya nairobi nebraska
nepal netherlands nevada newcastle nigeria nile nirvana normandy norway ohio oklahoma oman ontario
oregon osaka ottawa oxford pakistan palestine panama paraguay paris pennsylvania persia peru
philadelphia philippines phoenix poland portugal prague pretoria quebec queensland romania rome
russia rwanda saigon samoa santiago sardinia saudi scotland seattle seoul serbia shanghai siberia
sicily singapore slovakia slovenia somalia spain sri sudan suriname sweden switzerland sydney syria
tahiti taiwan tajikistan tanzania tasmania tehran tennessee texas thailand tibet tokyo tonga
toronto trinidad tunisia turkey turkmenistan uganda ukraine uruguay utah uzbekistan vancouver
venezuela venice vermont vietnam virginia wales warsaw washington wellington wyoming yemen yugoslavia
zambia zimbabwe
algorithm alphabet ampere amplitude anchor android angular animation anode antenna aperture append
archive arithmetic array assembly assertion async atom autopilot backend bandwidth banner batch
benchmark binary bitmap boolean bootstrap buffer bug bytecache cache callback capacitor cartridge
channel checksum cipher ciphertext clipboard clocking clone closure cluster codec codepoint collision
compiler compress concatenate concurrency conditional constant constructor container context
converter cookie coroutine coupling coverage crash cron crypt cryptography cursor daemon dashboard
deadlock debug debugger declarative decode decompile decorator decrypt delegate delimiter deployment
deprecation descriptor deserialize devops digest directive dispatcher distribution docker domain
downgrade driver dump dynamic emulator encapsulation encode encoder encryption endpoint enumerable
escalation eventloop exception executor expression extensible facade factory fallback fetch
filesystem filter firmware flag flowchart framework function garbage gateway generator git github
globals gradient graph greedy grid hardware hash hashing headless heap heartbeat heuristic hex
hierarchy histogram hook hostname hotspot hydration hypervisor idempotent identifier immutable
imperative import index inherit initialize inline instance instruction integer interpreter interrupt
invariant iteration iterator json kernel keychain keyword lambda latency layout lexer library
lifecycle linker lint listener literal lockfile logger loopback machine macro malloc manifest mapper
marshal memoization memory menu merge mesh metadata method middleware migration mime mirror mnemonic
mock model module monad monolith mutex namespace native neural node normalize npm null nullptr oauth
object observable offline onboarding opcode operand operator optimizer orchestration overflow
overload override packet padding pagination palette parallel parameter parser partition patch payload
peer permission persist pipeline pixel placeholder platform plugin pointer polling polymorphism
portal pragma precision predicate preprocessor primitive print priority process processor profile
programmer projection promise prompt propagate protocol prototype proxy pseudo publish pull pulse
puppet push quantum query queue race rack radix raft range raster reactive reactor reader readonly
rebase recursion redundant refactor referential regex registry regression reify relay release
remote render replica repository represent request resolver resource response restful retry reusable
revert rewrite ringbuffer rollback router runtime sandbox scaffolding scheduler schema scope script
scroll sdk segment semaphore serialize serverless session shader shard shell shim shortcut
signature singleton sketch slicing slot snapshot socket solid source spawn specification spectrum
spool stack stage stakeholder stamp state statement static stdin stdout storage stream string struct
stub submodule subscribe subscript subroutine subsystem subtree sudo supervisor surface suspended
swagger swap switch symbol syntax synthesis sysadmin syscall table tag tailgate target task team
telemetry template tensor terminal testable texture thread threshold throttle throughput timezone
token tombstone toolchain tooltip topology trace tracer track traffic transaction transcode
transducer transfer transform transistor transition translate transpile traverse tree trigger
truncate tunnel tuple tutorial typecheck typedef unicode unify unit unix upgrade upload upstream
url user utility uuid validator variable vector vendor version vertex virtual visibility vm volume
vulnerability wasm web webhook websocket widget wiki wildcard wire wireless worker workflow
workload workspace wrapper xpath yaml zip zlib zone zoom
apple apricot avocado banana blackberry blueberry boysenberry cantaloupe cherry coconut cranberry
currant date dragonfruit durian elderberry fig gooseberry grape grapefruit guava honeydew huckleberry
jackfruit kiwi kumquat lemon lime lychee mandarin mango mulberry nectarine olive orange papaya
passionfruit peach pear persimmon pineapple plantain plum pomegranate quince raspberry starfruit
strawberry tangelo tangerine watermelon
artichoke asparagus avocado basil beetroot broccoli cabbage carrot cauliflower celery chard chickpea
chili cilantro collard corn cucumber daikon dill eggplant endive fennel fenugreek garlic ginger
horseradish jicama kale kohlrabi leek lentil lettuce mustard okra onion parsley parsnip pea peanut
pepper potato pumpkin radicchio radish rhubarb rutabaga scallion shallot spinach squash tomato
turnip wasabi watercress yam zucchini
almond amaranth barley buckwheat cashew chestnut chia chickpea coconut couscous farro flax hazelnut
hemp kamut macadamia millet oat pecan pistachio quinoa rice rye sesame sorghum spelt sunflower
tahini teff triticale walnut wheat wildrice
amber amethyst aquamarine azure beige black blond blue brown burgundy celadon cerulean charcoal
chartreuse chocolate cobalt copper coral cream crimson cyan ebony ecru emerald fuchsia gold gray
green hazel indigo ivory jade khaki lavender lilac lime magenta mahogany maroon mauve mint navy
ochre olive orange orchid peach pearl pink plum purple red rose ruby russet saffron salmon sapphire
scarlet sepia sienna silver slate tan taupe teal turquoise umber violet viridian white yellow
admire adore affable affectionate agreeable amazing ambitious amiable amused analytical angelic
animated appreciative attentive authentic benevolent blissful bold brave bright brilliant buoyant
calm candid capable carefree careful caring cerebral charming cheerful chic chivalrous clever
compassionate composed confident congenial conscientious considerate content convivial cool
courageous courteous creative curious daring dashing dazzling debonair decisive dedicated delightful
dependable determined devoted diligent diplomatic discerning discreet dynamic earnest easygoing
ebullient eccentric educated efficient elegant eloquent empathetic energetic enlightened
enthusiastic ethical exacting excellent exceptional exciting expert exuberant fair faithful fantastic
fearless flexible focused forgiving forthright frank friendly frugal fun funny generous gentle
genuine gifted giving graceful gracious gregarious grounded happy hardy harmonious helpful heroic
honest honorable hopeful hospitable humble humorous idealistic imaginative impartial incisive
independent industrious ingenious innovative insightful inspiring intelligent intuitive inventive
jovial joyful jubilant judicious keen kind kindly knowledgeable laidback leaderly learned lighthearted
lively logical lovable loyal lucid magnanimous mellow meticulous mindful modest moral motivated
natural neat noble nonchalant nurturing objective observant open optimistic organized original
outgoing passionate patient peaceful perceptive persevering persistent personable philosophical
pioneering placid playful pleasant poised polished practical pragmatic precise principled proactive
proficient profound progressive prompt proper prosperous protective prudent punctual quirky radiant
rational receptive reflective relaxed reliable resilient resourceful respectful responsible
responsive reverent romantic sagacious sane scholarly scrappy sedate selfless sensible sensitive
sentimental serene sharp shrewd sincere skillful smart sociable solid soulful spirited spontaneous
sprightly stable steadfast steady stoic straightforward strategic studious sturdy suave sublime
subtle sunny supportive sweet sympathetic systematic tactful talented tenacious tender thoughtful
thrifty tolerant tranquil trustworthy truthful unbiased understanding unflappable unique unselfish
upbeat valiant versatile vigilant vigorous virtuous visionary vivacious warm welcoming whimsical
wholesome wise witty youthful zealous
achieve adjust admire advise analyze answer approve arrive ask assist attend balance bathe begin
behave believe belong bend bless blink boast boil borrow bounce bow brake breathe breed brighten
bring brush build burn buy calculate calm carry carve cast catch celebrate change chase chat cheer
chew choose clap clean climb close collect comb combine come command compare compete complain
complete compose compute conclude confess confirm connect consider construct consult continue
contribute convince cook copy count cover crawl create cross cry cut dance decide declare decorate
deliver demand describe deserve design desire destroy develop dig dine discover discuss dismiss
divide donate doubt draw dream dress drink drive drop dry earn eat educate elect embrace employ
encourage end enjoy enter entertain escape examine exchange excite excuse exercise exist expand
expect explain explore express extend face fail fall fasten favor fear feed feel fetch fight fill
find finish fish fix flee float flow fly fold follow forbid forget forgive form freeze gather gaze
give glow govern grab greet grin grow guard guess guide hammer hand handle hang happen harvest hate
heal hear heat help hide hit hold hop hope hug hunt hurry hurt ignore imagine imitate improve
include increase inform inherit inject injure inquire inspire install invent invest invite iron
jog join joke judge jump keep kick kiss kneel knit knock know laugh launch lay lead lean leap learn
leave lend lift light listen live look lose love lower maintain make manage march marry measure
meet melt mention mind miss mix mold move mow name nap navigate need nod notice obey observe obtain
occur offer open operate order organize overcome owe own pack paint pardon participate pass pause
pay peel perform permit persuade pick place plan plant play please plough pluck plug point polish
ponder pour practice praise pray preach prepare present preserve press pretend prevent print
proceed produce promise pronounce protect prove provide publish pull punch purchase push question
quit race raise reach read realize rebuild recall receive recite recognize recommend record
recover reduce refill reflect refuse regret rehearse reject relax release rely remain remember
remind remove renew rent repair repeat replace reply report request rescue research resist rest
restore retire return reveal reverse review revise reward ride ring rinse rise risk roast rock
roll rub ruin rule run rush sail salute sample save say scan scare scatter scold scoop scrape
scratch scream scrub seal search seat secure see seek seem seize select sell send separate serve
set settle sew shake share sharpen shave shed shine shiver shop shout show shrink shrug shuffle
shut sigh sign sing sink sip sit sketch skip slam sleep slice slide slip smell smile smoke snap
sneeze sniff snow soak solve sort sow speak spell spend spill spin spit splash split spoil spray
spread spring sprinkle sprint squeeze stack stand stare start starve stay steal steer stick sting
stir stop store stretch stride strike stroll study stumble stun submit succeed suck suggest suit
supply support suppose surprise survive swallow swap swear sweep swim swing switch take talk tame
tap taste teach tear tease telephone tell tempt test thank thaw think threaten throw tickle tidy
tie tip tire toast toss touch trace train translate travel treat tremble trim trip trot trust try
tuck tumble turn twist type understand undo unfold unite unlock unpack unveil upgrade urge use
value vanish vary visit voice volunteer vote wait wake walk wander want warm warn wash waste
watch water wave weave weep weigh welcome whip whisper whistle win wind wink wipe wish wonder
work worry wrap wreck write yell yield zoom
"""

REAL_WORDS_5000_B = """
aardvark alpaca anteater antelope armadillo baboon badger bat bear beaver bison boar buffalo
bull camel caribou cat cheetah chimpanzee chinchilla chipmunk cougar cow coyote deer dingo
dolphin donkey dormouse elephant elk ermine ferret fox gazelle gerbil giraffe goat gopher
gorilla groundhog hamster hare hedgehog hippopotamus horse hyena ibex jackal jaguar kangaroo
koala lemming lemur leopard lion llama lynx manatee marmot marten meerkat mink mole mongoose
monkey moose mouse mule muskrat ocelot okapi opossum orangutan otter ox panda panther pig
platypus porcupine porpoise possum prairie puma rabbit raccoon ram rat reindeer rhinoceros
seal sheep shrew skunk sloth squirrel tapir tiger vole walrus warthog weasel whale wolf
wolverine wombat woodchuck yak zebra
albatross blackbird bluebird bluejay buzzard canary cardinal cassowary chickadee chicken condor
cormorant crane crow cuckoo dove duck eagle egret emu falcon finch flamingo goose goshawk
grouse gull hawk heron hummingbird ibis jay kestrel kingfisher kiwi lark loon magpie mallard
mockingbird nightingale nuthatch oriole osprey ostrich owl parakeet parrot partridge peacock
pelican penguin pheasant pigeon puffin quail raven roadrunner robin rook seagull sparrow
starling stork swallow swan swift tern toucan turkey vulture woodpecker wren
anchovy angelfish barnacle bass clam cod coral crab crayfish cuttlefish eel flounder goldfish
haddock halibut herring jellyfish kelp lobster mackerel marlin mussel octopus oyster perch pike
plankton pollock prawn salmon sardine scallop shark shrimp squid starfish stingray sturgeon
swordfish trout tuna urchin walleye
ant aphid bee beetle bumblebee butterfly caterpillar centipede cicada cockroach cricket damselfly
dragonfly earwig firefly flea fly gnat grasshopper hornet katydid ladybug locust louse mantis
mayfly midge millipede mite mosquito moth scorpion silverfish spider tarantula termite tick wasp
weevil
alligator chameleon cobra crocodile frog gecko iguana lizard newt python rattlesnake salamander
snake tadpole toad tortoise turtle viper
acacia alder ash aspen banyan baobab beech birch bonsai boxwood cactus cedar cherry chestnut
cypress dogwood ebony elm eucalyptus fern fir hawthorn hazel hemlock hickory holly ironwood ivy
juniper larch laurel magnolia mahogany maple mangrove mesquite moss myrtle oak oleander palm
pecan pine poplar redwood rosewood rowan sassafras sequoia spruce sycamore tamarind teak walnut
willow yew
aster azalea begonia bluebell buttercup camellia carnation chrysanthemum clematis crocus daffodil
dahlia daisy dandelion delphinium foxglove freesia gardenia geranium gladiolus hibiscus hyacinth
hydrangea iris jasmine lavender lilac lily lotus marigold narcissus orchid pansy peony petunia
poinsettia poppy primrose snapdragon sunflower tulip violet wisteria zinnia
accountant acrobat actuary admiral ambassador analyst anthropologist archaeologist architect
archivist astronaut astronomer athlete auditor baker banker barber bartender biologist blacksmith
botanist broadcaster builder butcher butler cabinetmaker captain carpenter cartographer cashier
chemist chiropractor choreographer cobbler comedian composer conductor consultant contractor
correspondent curator decorator dentist designer detective dietician diplomat drummer economist
electrician engineer entrepreneur examiner farmer firefighter fisherman florist foreman gardener
geologist glassblower goldsmith grocer guitarist hairdresser historian hunter illustrator
inspector instructor interpreter inventor investigator janitor jeweler journalist lecturer
librarian lifeguard linguist locksmith lumberjack magician manager mason mechanic merchant
meteorologist midwife miner musician novelist nutritionist optician pharmacist philosopher
photographer physician physicist pianist pilot plumber policeman politician porter preacher
printer professor programmer psychiatrist publisher rancher receptionist reporter researcher
sailor scientist sculptor secretary sergeant shoemaker singer surgeon surveyor tailor technician
therapist translator tutor veterinarian violinist watchmaker welder zoologist
archery athletics badminton bowling boxing cycling diving fencing gymnastics handball hockey judo
karate lacrosse marathon polo racquetball rowing rugby sailing skateboarding skiing snowboarding
softball squash surfing swimming taekwondo volleyball weightlifting wrestling
accordion bagpipe banjo bassoon bell bongo bugle cello clarinet cymbal dulcimer fife flute gong
harmonica harp harpsichord lute lyre mandolin oboe organ piccolo recorder saxophone sitar
tambourine theremin trombone trumpet tuba ukulele vibraphone viola xylophone zither
anvil axe awl bolt broach chisel clamp crowbar cutter drill file hatchet hacksaw hoe jack jigsaw
lathe level mallet nail nut pickaxe plane pliers punch rake rasp rivet saw scissors screw
screwdriver scythe shovel sickle spade staple tack tape tongs trowel vise wedge wrench
apron ascot bandana belt beret blazer blouse bonnet boot bowtie bra bracelet brooch buckle cap
cape cardigan cloak corset cravat cuff diaper dungarees earring gloves gown headband helmet hood
hoodie jersey jumper kilt kimono laces leotard mittens necklace nightgown overalls pajamas parka
poncho pouch pullover purse raincoat robe sandal sarong sash scarf shawl shorts slacks slippers
sneakers sock stole stocking sweater swimsuit tights trousers tunic turban veil vest waistcoat
wallet wristband zipper
avalanche blizzard breeze cloudburst cyclone dew downpour drizzle drought earthquake flood fog
frost gale hail haze hurricane lightning mist monsoon overcast rainbow sandstorm shower sleet
slush smog snowflake storm sunlight sunrise sunset thunder tornado tsunami typhoon whirlwind
abdomen ankle aorta appendix artery backbone bicep bladder blood bone brain breast calf capillary
cartilage cheek chest chin cochlea colon cornea cranium ear elbow esophagus eyelash eyebrow
eyelid femur finger foot forehead gallbladder gland groin gum hair hand heart heel hip intestine
jaw joint kidney knee knuckle larynx leg ligament lip liver lung marrow muscle nail navel nerve
nose nostril pancreas pelvis pharynx pupil retina rib scalp shoulder skeleton skin skull spine
spleen stomach tendon thigh throat thumb thyroid toe tongue tonsil tooth torso trachea vein
vertebra waist wrist
allergy analgesic anesthesia antibiotic antidote antiseptic aspirin asthma biopsy bronchitis
cataract chemotherapy cholera concussion cough diabetes diagnosis diarrhea dizziness dysentery
eczema edema epidemic epilepsy fever flu fracture gastritis glaucoma headache hepatitis herpes
hypertension immunity infection inflammation influenza injection insomnia insulin leukemia
malaria measles migraine nausea obesity pandemic paralysis plague pneumonia polio prescription
rabies rash recovery remedy sedative seizure smallpox sprain stroke surgery symptom syndrome
tetanus therapy tuberculosis tumor vaccine virus wound
affidavit alibi appeal arrest bailiff bankruptcy barrister bench brief charge claim client
complaint counsel custody damages defendant defense deposition discovery docket evidence felony
grievance hearing indictment injunction judgment jury lawsuit legal legislation liability
litigation magistrate misdemeanor motion notary oath objection offense parole perjury petition
plaintiff plea precedent probation prosecutor restitution ruling sentence settlement subpoena
testimony tort trial verdict warrant witness
airman ammunition armor arsenal artillery battalion battle bayonet brigade bullet cannon cavalry
colonel combat commander company corps deployment division drill enemy ensign flank fort
fortification garrison general grenade gunner infantry invasion lieutenant major marine missile
munitions offensive patrol platoon private raid recruit regiment retreat rifle sabre siege sniper
squad strategy tactic tank torpedo trench troop veteran victory warfare weapon
anchor barge beacon berth bow brig buoy cabin canoe canvas capsize cargo catamaran compass crew
cruise cutter deck dinghy dock ferry fleet freighter galley gangway gunwale harbor hatch helm
jetty kayak keel knot lagoon launch lighthouse liner logbook mast mooring oar outrigger paddle
pier plank pontoon port prow quay raft rigging rowboat rudder sail schooner sextant ship shoal
skipper sloop starboard stern surf tack tender tug vessel voyage wharf yacht
bake barbecue baste beat blend boil braise broil brown brush carve chill chop coat cream cube cut
debone decorate dice dilute drain dredge drizzle dust fillet flake flour fold garnish glaze grate
grease grill grind knead marinate mash melt mince mix parboil peel pickle pinch pipe pit poach
pound puree reduce refresh roast saute scald score sear season shave sift simmer skim slice
smoke soak spritz steam stew stir strain stuff sweat thicken toast toss truss whip whisk zest
alcove arch attic balcony balustrade basement buttress ceiling chimney column colonnade corridor
courtyard cupola dome doorway eave facade foyer gable gazebo hallway hearth lintel loggia mansard
mezzanine minaret nave niche parapet patio pediment pergola pillar portico rotunda spire
stairwell terrace threshold transom turret vault veranda vestibule
acetate acid alkali alkane alkene alkyne alloy aluminum ammonia argon arsenic atom barium base
beryllium bismuth boron bromine cadmium calcium carbon catalyst cation chlorine chromium cobalt
compound copper corrosion crystal dilute distillation electron element emulsion enzyme ethanol
fluoride gallium germanium glucose gold graphite helium hydrogen hydroxide iodine iridium iron
isotope lanthanum lead lithium magnesium manganese mercury methane molecule molybdenum neon
nickel nitrate nitrogen noble osmium oxidation oxygen palladium phosphate phosphorus platinum
plutonium potassium precipitate propane protein radium radon reagent rubidium ruthenium salt
scandium selenium silicon silver sodium solution solvent strontium sulfate sulfur tantalum
technetium tellurium thallium tin titanium tungsten uranium vanadium xenon yttrium zinc
zirconium
abacus algebra angle apex arc area arithmetic asymmetry average axiom axis binomial calculus
chord circumference coefficient combination conic constant coordinate cosine cube curve decimal
denominator derivative diagonal diameter differential digit dimension divide divisor domain
ellipse equation exponent factor factorial fraction function geometry graph hexagon hyperbola
hypothesis integer integral intersect inverse irrational lemma limit logarithm matrix maximum
median minimum minus modulus multiply numerator octagon oval parabola parallel parallelogram
pentagon percentage perimeter permutation perpendicular plane polygon polynomial prime
probability product proof proportion protractor pyramid quadrant quadratic quotient radian radius
ratio rational rectangle rhombus root scalar sequence series sine slope solid sphere square
subset subtract sum tangent tetrahedron theorem trapezoid triangle trigonometry vector velocity
vertex volume
aeon annum autumn dawn daybreak decade dusk epoch equinox fortnight hour instant interval midday
midnight millennium minute moment month morning noon nightfall period quarter season second
solstice spring summer twilight week weekend winter year
admiration affection agony amusement anger angst anguish annoyance anticipation anxiety apathy
apprehension awe bitterness bliss boredom calmness cheer comfort compassion contempt contentment
courage craving curiosity delight depression desire despair disgust dread ecstasy elation
embarrassment empathy enthusiasm envy euphoria excitement fear frustration fury gladness glee
gratitude grief guilt happiness hatred homesickness hope horror hostility humility hurt
indignation infatuation insecurity irritation jealousy joy loneliness longing love lust
melancholy misery nostalgia optimism panic passion pessimism pity pleasure pride rage regret
relief remorse resentment resignation sadness satisfaction serenity shame sorrow spite surprise
suspense sympathy tension terror triumph unease wonder worry zeal
abruptly absolutely accordingly accurately acutely adamantly additionally adequately admirably
admittedly affectionately aggressively alternatively amazingly ambitiously angrily annually
anxiously apparently appropriately approximately arrogantly assertively attentively automatically
awfully barely basically beautifully bitterly blindly boldly bravely briefly brightly brilliantly
busily calmly candidly carefully carelessly casually cautiously certainly cheerfully cleverly
closely clumsily comfortably commonly compassionately completely confidently consequently
considerably consistently constantly continually conveniently correctly courageously curiously
currently daily dangerously deeply definitely deliberately delicately densely desperately
diligently directly discreetly distinctly dramatically eagerly earnestly easily economically
effectively efficiently elegantly eloquently emotionally energetically enormously entirely
equally essentially eventually evidently exactly exceedingly excessively excitedly exclusively
explicitly extremely faithfully famously fearlessly fiercely finally firmly fondly foolishly
formally fortunately frankly frantically frequently frugally fully furiously generally generously
gently gladly gleefully globally gracefully gradually gratefully greatly greedily happily hardly
hastily heavily hesitantly honestly hopefully hospitably hourly humbly hurriedly immediately
impatiently imperfectly implicitly improperly incidentally increasingly incredibly independently
indirectly individually inevitably informally initially innocently instantly intensely
intentionally intently interestingly internally invariably irritably joyfully joyously jubilantly
justly keenly kindly largely lately lazily legally lightly likely literally logically loudly
lovingly loyally luckily madly mainly manually marginally massively maturely mechanically
mentally merrily methodically meticulously mildly mindfully miserably moderately modestly monthly
morally mostly mysteriously naturally nearly neatly nervously newly nobly normally notably
noticeably obediently obviously occasionally officially openly optimistically ordinarily
originally painfully partially patiently peacefully perfectly permanently persistently personally
physically playfully pleasantly politely poorly positively possibly potentially powerfully
practically precisely predictably presently previously primarily privately probably
professionally profoundly promptly properly proudly publicly punctually purely quickly quietly
rapidly rarely rationally readily really reasonably recently recklessly regularly relatively
reluctantly remarkably repeatedly reportedly resolutely respectfully richly rightly roughly
routinely rudely sadly safely scarcely scientifically secretly securely seldom sensibly
sensitively seriously sharply shortly shyly significantly silently similarly simply sincerely
skillfully slowly smoothly softly solemnly sometimes soon soundly specifically speedily
spiritually splendidly steadily sternly strangely strictly strongly stubbornly successfully
suddenly sufficiently suitably surely surprisingly suspiciously swiftly sympathetically
systematically tactfully temporarily tenderly terribly thankfully thoughtfully tightly timidly
tolerantly totally traditionally tragically tranquilly truly typically ultimately unbelievably
uncomfortably undoubtedly unexpectedly unfortunately uniquely universally unusually urgently
usually utterly vaguely valiantly vastly verbally violently virtually visibly vividly voluntarily
warmly weakly wearily weekly wholly wildly willingly wisely wonderfully worriedly yearly
zealously
abate abbreviate abdicate abduct abhor abide abolish abridge absolve abstain abstract abuse
accelerate accentuate acclaim accommodate accompany accumulate accuse acquaint activate adapt
adhere adjourn admonish adorn advocate affiliate affirm afflict aggravate agitate alienate align
allege alleviate allocate allot allude alter amass amend amplify amuse annex annihilate annul
anticipate applaud appraise apprehend approximate arbitrate arouse articulate ascertain aspire
assemble assimilate assuage atone attest attribute augment authorize avert avoid await awaken
baffle banish bargain batter beckon befriend begrudge belittle bemoan bequeath bereave beseech
besiege bestow betray beware bewilder blaspheme blazon blunder bolster bombard brace brandish
breach bribe broaden browse bruise budge bulge bungle burgeon burrow bustle cajole calibrate
captivate castigate catalogue categorize cater caress cede cement censor chastise cherish chide
chronicle circulate circumvent clarify classify cleanse cleave cling cloak coerce cogitate
coincide collaborate collate collide commemorate commence commend commiserate commission commute
compel compensate compile complement complicate compliment comport comprehend compress comprise
concatenate concede conceive conceptualize conciliate concur condemn condense condone confer
confide configure confine confiscate conflate conform confound congratulate conjure connote
conquer consecrate conserve consign consolidate conspire constrain construe contemplate contend
contort contradict contravene contrive converge converse convolve coordinate corroborate corrode
counter counteract covet cower cringe critique crumple cultivate curb curtail dampen dangle dart
daunt dazzle debase debate debilitate decapitate decay deceive decelerate decipher decode
decompose decree decry dedicate deduce defame default defecate defer define deflate deflect
deform defraud defray defuse defy degrade dehumidify dehydrate deify delegate delete deliberate
delineate delude delve demean demolish demonstrate demote denote denounce dent depict deplete
deplore deploy depose deprive deputize deride derive descend desecrate designate despise
destabilize detach detain deteriorate detract devalue devastate deviate devise devolve devour
dictate differentiate diffuse digest dilate diminish din disabuse disallow disapprove disarm
disassemble disavow discard discern discharge disclaim disclose discolor discomfit disconnect
discontinue discount discourage discredit discriminate disdain disembark disengage disentangle
disfigure disgrace disgruntle disguise dishearten disinfect disintegrate disinter dislike
dislocate dislodge dismantle dismay dismember disobey disorganize disorient dispatch dispel
dispense disperse displace disprove dispute disqualify disregard disrobe disrupt dissect
disseminate dissent dissipate dissociate dissolve dissuade distill distinguish distort distract
distress distribute distrust disturb disunite divert divest divulge document dominate donate
doodle dovetail doze dredge drench dribble drift droop drudge dub dwindle dye ease eavesdrop ebb
eclipse economize edify efface eject elaborate elapse electrify elevate elicit elope elucidate
elude emanate emancipate embark embellish embezzle embody embolden emboss emigrate emit emphasize
employ empower emulate enable enact encase enchant encircle enclose encompass encounter encroach
encrypt endeavor endorse endow endure energize enforce engender engrave engross engulf enhance
enjoin enlighten enlist enliven enmesh enrage enrich enroll ensnare ensue ensure entail entangle
enthrall entice entitle entomb entrap entreat entrench entrust enumerate envision epitomize
equate equip eradicate erase erect erode erupt escalate escort espouse esteem estimate etch
evade evaporate evict evoke evolve exacerbate exact exalt exasperate excavate exceed excel
excerpt excise exclaim exclude excoriate excrete exculpate execrate exemplify exempt exert
exhale exhume exonerate exorcise expand expatriate expel expend expiate expire explicate
explode exploit expound expose expropriate expunge expurgate extenuate exterminate extinguish
extol extort extract extrapolate exude exult fabricate facilitate factorize falsify falter
familiarize fasten fathom fatigue fawn feign felicitate ferment fertilize fester fiddle filter
finance flabbergast flail flare flatten flatter flaunt flavor flicker flinch flit flock flounder
flourish flout fluctuate flutter foil foment forage forbear forearm foreclose forego foresee
foreshadow forestall forfeit forge formulate forsake fortify foster founder fragment franchise
fraternize fret frighten frolic frustrate fulfill fumble fumigate funnel furnish fuse gabble
gallop galvanize garner gasp gesticulate giggle gird glance glare glaze glean glimmer glimpse
glisten glitter glorify gloss glut gnaw goad gobble gorge grapple gratify gravitate graze grieve
grimace grind groan groom grope grouse grovel growl grumble grunt gulp gush haggle halve hamper
hanker harass harden harmonize harness harrow hasten hatch haul haunt hazard heave heckle heighten
herald hesitate hijack hinder hinge hoard hoist holler hone hoodwink hoop hoot hover howl huddle
hurl hurtle hush hustle hybridize hypnotize idealize ignite illuminate illustrate imagine imbibe
imbue immerse immigrate immunize impair impale impart impede impel imperil impersonate implicate
implore importune impose impoverish imprecate impregnate impress imprint imprison improvise
impute inaugurate incinerate incise incite incline incorporate incriminate incubate inculcate
incur indemnify indent indict indoctrinate induce indulge infect infest infiltrate inflame
inflate inflict infringe infuse ingest inhale inhibit initiate inject injure inlay innovate
inoculate inscribe inseminate insinuate inspect instigate instill insulate intensify intercept
interchange intercede interject interlace interlock intermingle interpose interrogate intersect
intersperse intertwine intimidate intone intoxicate intrench intrude inundate inveigh invert
investigate invigorate invoke irk irrigate iterate jab jabber jangle jeer jeopardize jettison
jingle jolt jostle jot jubilate juggle juxtapose keel kindle kowtow lace lag lament laminate
languish lapse lash laud lavish leach lease legalize legislate legitimize lengthen lessen levy
liberate license lighten limp linger liquefy lisp loathe lob lobby localize loiter loom loosen
loot lubricate lug lull lumber lure lurk luxuriate magnify malign malinger mandate maneuver
mangle manifest manipulate marinate maroon marshal marvel mask materialize maul meander mediate
meditate meld mellow memorize menace mend merge mesh mesmerize migrate mime mimic mingle
minimize mint mirror misappropriate misbehave miscalculate misdiagnose misdirect misfire misguide
mishandle misinform misinterpret misjudge mislead misplace misprint misquote misread
misrepresent misspell mistreat mistrust misuse mitigate moan mobilize mock modulate moisten mold
mollify molt monopolize moor motivate motor mound mound mount mumble munch murmur muster mutate
mutilate mutter nag narrate navigate neaten necessitate negate neglect negotiate nestle nibble
niggle nip nominate normalize notch notify nudge nullify numb nurture obey obfuscate obligate
oblige obliterate obscure obsess obstruct obtain obtrude obviate occupy offend officiate offset
ogle ooze opine oppose oppress optimize orbit orchestrate ordain orient originate ornament
oscillate oust outdo outgrow outlast outlive outmaneuver outnumber outpace outperform outrun
outsell outshine outsmart outstrip outwit overawe overbear overburden overcharge overdo overeat
overestimate overflow overhang overhaul overhear overheat overjoy overlap overload overpower
overrate overreach override overrule oversee overshadow overshoot oversimplify oversleep
overstate overstay overstep overtake overthrow overturn overvalue overwhelm overwork pacify
package paddle padlock paginate pain palliate palpitate pamper pander paralyze parboil parch
pardon pare parody parry parse partake participate partition paste patch patent patronize pattern
pave pawn peck pedal peek peep penetrate perch percolate perfect perforate perfume peril perish
permeate perpetuate perplex persecute persevere persist personalize personify pertain perturb
peruse pervade pervert petition petrify philosophize photocopy photograph picket pilfer pillage
pinch pique pitch pivot placate plagiarize plague plank plaster plat plead pledge plow pluck
plumb plummet plunk ply poach poise polarize pollinate pollute ponder populate pore portend
portion portray posit postulate pounce pout prance prattle precede precipitate preclude predate
predict predispose predominate preen preface prefigure prefix preheat prejudge prejudice
prelude premeditate premiere preoccupy prepare preponderate prepossess prepay prescribe preside
pressure presume presuppose pretend prevail prevaricate preview prey prick prickle prime primp
prioritize prise procrastinate procure prod profess proffer prognosticate proliferate prolong
promenade promulgate propel prophesy propound proscribe prosecute prosper provoke prowl prune
pry publicize pucker puff pulsate pulverize pummel puncture purge purify purport purvey putrefy
quantify quarantine quash quaver quell quench query quibble quicken quiver quiz radiate rally
ramble ramp ransack rant rap ratify ration rationalize rattle ravage rave ravel realign reap
reappear rearrange reassemble reassert reassess reassign rebate rebuff rebuke recalibrate recant
recap recapture recede recharge recidivate reciprocate recite reckon reclaim recline recompense
reconcile reconsider reconstruct recount recoup recreate recruit rectify recuperate recur recycle
redeem redefine redesign redirect rediscover redistribute redouble redound redress reek reel
refashion refill refine refract refrain refresh refute regain regenerate regress rehash rehearse
reimburse rein reinstate reiterate rejoice rejuvenate relapse relay relegate relent relinquish
relish reload relocate remake remarry remedy reminisce remit remodel remonstrate remunerate
renege renounce renovate reorder reorganize repeal repel repent rephrase replay replenish
replicate repose repress reprimand reprint reproach reproduce reprove repudiate repulse
requisition rescind resent reside resign resonate respire restart restate restrain restrict
restructure resurrect retaliate retard reteach retort retract retrieve reunite revel revenge
reverberate revere revert revile revive revoke revolt revolutionize revolve rhyme ridicule rig
rinse riot ripen ripple rival rivet roam roar romp rotate rouse rove ruffle ruminate rummage
rupture rustle sabotage sadden saddle safeguard salivate sally sanctify sanction sanitize sap
sashay satiate satirize saturate saunter savage savor scamper scandalize scavenge scintillate
scoff scoot scorch scour scout scowl scramble screech scribble scrimp scrounge scrutinize scuff
sculpt scurry secede seclude secrete sedate seduce seep seethe sequester serenade sever shackle
sharpen shatter shear sheathe shelve shepherd shirk shiver shred shriek shuck shudder shun shunt
shutter sicken sidestep sift signify singe situate skew skid skim skirmish skulk slack slander
slant slash slate slaughter slay sled sling slink slit slither slog slosh slouch slug slumber
slump smack smear smite smolder smother smudge smuggle snag snarl snatch sneer snip snooze
snore snort snub snuff soar sober socialize soften solder solicit solidify soothe sough sow span
sparkle spatter spawn specialize specify speckle speculate spew spike spiral splash splatter
splay splice splinter sponsor spook spool spout sprain sprawl sprig sprinkle sprout spruce spur
spurn sputter squabble squander squat squawk squeak squeal squelch squint squirm squirt
stabilize stagger stagnate stain stammer stampede standardize startle stash stave steady stencil
stereotype sterilize stifle stimulate stipulate stitch stoke stomp stoop stow straddle straggle
straighten strangle strategize stray streak strengthen strew stride strive strut stub stupefy
stutter subdue submerge subordinate subside subsidize subsist substantiate subsume subvert
succor succumb suffice suffocate sulk sully summarize summon sup supercharge supersede supervise
supplant supplement supplicate suppress surge surmise surmount surpass surrender survey survive
suspect suspend sustain swamp swat sway sweat sweeten swelter swerve swindle swirl swoop
symbolize sympathize synchronize syndicate synthesize systematize tabulate taint tally tamper
tang tangle tarnish tarry tattle taunt telegraph televise temper tender terminate terrify
testify thicken thirst thrash thrill throb throng thwart tickle tidy tighten tilt tinker tint
tolerate toil toll toot topple torment torture totter toughen tout tow tower toy trace track
trade trail trample transact transcend transcribe transgress transmit transmute transpire
transplant transpose traverse travesty tread treble tremble trench trespass trickle trifle trim
triple trivialize trounce trudge trump truncate tuck tug tune tussle twinkle twirl twitch typify
tyrannize unarm unbend unbind unbolt unburden unbutton uncap unchain unclasp uncoil uncover
uncross undress undulate unfasten unfurl unhinge unify unlace unleash unload unmask unpack
unplug unravel unroll unseat unsettle untangle untie unwind unwrap upbraid update upend uphold
uproot upset usher usurp utilize utter vacate vacillate validate valorize vandalize vanquish
vaporize vault veer vend veneer venerate venture verbalize verify vex vibrate victimize vie
vilify vindicate violate visualize vitiate vivify vocalize vouch vouchsafe vow vulgarize wade
waffle waft wag wage wager wail waive wallow waltz wane warble ward warp waver wax weaken wean
weary weather wedge weed welcome weld welter wend whack wheedle wheel wheeze whet whimper whine
whirl whisk whiten whittle widen wield wiggle wilt wince wink winnow wipe wire wither withhold
withstand wobble woo wrangle wreak wrench wrest wrestle wriggle wring wrinkle writhe yank yawn
yearn yodel zap zero zip
abidjan abuja accra addis adelaide algiers amman ankara antananarivo apia ashgabat asmara
asuncion auckland baku bamako bandar bangui banjul basseterre belfast belmopan bergen bern
bilbao bishkek bissau bogota bratislava brasilia brazzaville bridgetown brisbane bucharest
budapest bujumbura canberra caracas cardiff castries chisinau conakry copenhagen cotonou dakar
damascus dhaka djibouti dodoma doha dublin dushanbe edinburgh freetown funafuti gaborone
georgetown guatemala hanoi harare havana helsinki honiara islamabad jakarta jerusalem juba
kabul kampala kathmandu khartoum kigali kingston kingstown kinshasa kuala kuwait kyiv libreville
lilongwe lima lisbon ljubljana lome luanda lusaka madrid majuro malabo male managua manama
manila maputo maseru mascat mbabane melekeok mexico minsk mogadishu monaco monrovia montevideo
moroni muscat nairobi naypyidaw ndjamena niamey nicosia nouakchott nukualofa oslo ottawa
ouagadougou palikir panama paramaribo paris phnom podgorica porto prague praia pretoria
pyongyang quito rabat reykjavik riga riyadh rome roseau santiago santo sarajevo seoul singapore
skopje sofia stockholm succo suva taipei tallinn tarawa tashkent tbilisi tegucigalpa tehran
thimphu tirana tokyo tripoli tunis ulaanbaatar vaduz valletta vatican victoria vienna vientiane
vilnius warsaw wellington windhoek yamoussoukro yaounde yaren yerevan zagreb zimbabwe
"""

# ==================================================================
# ★ REAL WORDS — EMBEDDED BATCHES C, D, E, F, G, J, K, L
# ==================================================================

REAL_WORDS_5000_C = """
table chair sofa couch bench stool recliner ottoman chaise loveseat settee futon
hammock rocker armchair wingchair footstool pouf beanbag mattress pillow cushion
duvet comforter quilt blanket sheet bedspread bedframe headboard footboard canopy
bunk trundle crib cradle bassinet wardrobe closet armoire dresser chest drawer
nightstand vanity hutch sideboard credenza buffet cabinet cupboard shelf rack
bookcase bookshelf mantel fireplace hearth stove oven range cooktop microwave
dishwasher refrigerator freezer toaster blender mixer grinder processor kettle
teapot coffeemaker percolator espresso frenchpress skillet saucepan stockpot
casserole dutchie wok griddle broiler rotisserie steamer colander sieve strainer
ladle spatula whisk tongs peeler grater mandoline mortar pestle rolling pin
cuttingboard choppingblock butcherblock breadbox canister jar bottle thermos
flask tumbler goblet chalice stein mug cup saucer teacup coffee cup plate bowl
platter dish saucer ramekin tureen gravyboat saltcellar pepper mill napkin
placemat coaster tablecloth runner trivet candleholder candelabra sconce
chandelier lampshade lantern flashlight torch floodlight spotlight desk lamp
floor lamp bedside lamp fairy lights pendant pendantlight dimmer switch outlet
socket plug cord cable wire adapter charger extension powerstrip surgeprotector
television monitor screen projector speaker soundbar subwoofer amplifier
receiver turntable record player cassette player cdplayer radio boombox
walkman headphones earbuds headset microphone webcam tripod selfiestick camera
lens flash shutter tripod camcorder drone printer scanner copier fax shredder
laminator labelmaker stapler holepunch binder folder clipboard whiteboard
chalkboard corkboard bulletin pinboard thumbtack pushpin paperclip binderclip
rubberband ruler protractor compass calculator abacus slide rule pencil pen
marker highlighter crayon chalk eraser sharpener inkwell quill fountain pen
ballpoint gel pen rollerball mechanical pencil lead graphite charcoal pastel
watercolor gouache acrylic oil paint canvas easel palette brushes sketchpad
notebook journal diary ledger planner calendar organizer filofax binder folder
envelope stamp postcard letter parcel package box carton crate barrel drum
bucket pail basket hamper bin trashcan wastebin dumpster recycling compost
mop broom dustpan vacuum sweeper scrub brush sponge rag cloth towel washcloth
handtowel bathmat showercurtain loofah soap dispenser toothbrush toothpaste
floss mouthwash razor shavingcream aftershave lotion perfume cologne deodorant
shampoo conditioner hairbrush comb hairdryer straightener curler scissors
clippers tweezers nailfile manicure pedicure cottonball qtip tissues wipes
diaper wipe bib pacifier bottle sippy highchair stroller crib mobile rattle
teether playpen playmat toy blocks legos duplo puzzle chess checkers backgammon
dominoes dice cards deck shuffleboard darts billiards pool snooker foosball
airhockey pingpong tabletennis badminton volleyball basketball soccer football
rugby cricket baseball softball tennis racket bat glove helmet pads jersey
cleats sneakers boots sandals flipflops slippers loafers oxfords brogues
moccasins wedges heels pumps stilettos platforms espadrilles clogs galoshes
wellingtons rainboots snowboots hikers trailrunners trainers runners joggers
belt buckle suspenders necktie bowtie cravat ascot scarf muffler shawl wrap
poncho cape cloak coat jacket blazer sportcoat windbreaker parka anorak
trenchcoat overcoat topcoat peacoat dufflecoat raincoat slicker vest waistcoat
cardigan pullover sweater jumper sweatshirt hoodie tank top camisole blouse
shirt tshirt polo henley flannel dress gown frock skirt kilt tutu petticoat
crinoline bustle corset brassiere lingerie underwear boxers briefs panties
leggings tights stockings pantyhose socks slippers robe bathrobe kimono sari
saree dirndl lederhosen toga sarong pareo dashiki caftan muumuu jumper romper
overalls coveralls jumpsuit wetsuit snowsuit spacesuit
jewelry bracelet bangle anklet armband brooch pin pendant locket necklace
choker torque chain earring stud hoop ring band signet engagement wedding
crown tiara diadem circlet coronet mitre turban fez beret cap hat bonnet
beanie fedora trilby panama bowler derby stetson sombrero boater cloche
visor helmet hardhat motorcycle helmet facemask goggles monocle spectacles
sunglasses reading glasses contact lens binoculars telescope microscope
periscope kaleidoscope magnifier loupe
wallet purse clutch satchel handbag tote duffel backpack knapsack rucksack
briefcase attache portmanteau trunk valise suitcase garment bag weekender
umbrella parasol cane walkingstick crutch staff crook shepherdshook
fork spoon knife spork chopsticks butterknife steak knife paring knife
cleaver boning knife bread knife fillet knife chef knife utility knife
pocketknife swissarmy jackknife switchblade bayonet dagger stiletto dagger
sword saber rapier katana scimitar cutlass claymore broadsword foil epee
shield buckler targe aegis breastplate cuirass greaves gauntlet visor helm
armor mail chainmail plate mail
hammer mallet sledgehammer tackhammer clawhammer ballpeen crosspeen
wrench spanner pliers pincers nippers snips shears scissors tin snips
screwdriver chisel gouge awl punch broach reamer countersink tap die
drill brace bit auger gimlet hole saw holesaw hacksaw coping saw jigsaw
circular saw chainsaw tablesaw bandsaw miter saw radial saw backsaw
plane spokeshave drawknife rasp file wood rasp metal file nail set
clamp vise c clamp bar clamp spring clamp pipe clamp welding clamp
level plumb bob square try square combination square bevel protractor
tape measure ruler yardstick calipers micrometer depth gauge feeler gauge
sandpaper sandblock sanding belt orbital sander belt sander palm sander
paintbrush roller tray ladder stepladder extension ladder scaffold
wheelbarrow crowbar prybar wrecking bar jemmy pickaxe mattock hoe rake
shovel spade trowel edger cultivator weeder aerator sprinkler hose nozzle
sickle scythe machete billhook axe hatchet tomahawk splitting maul wedge
anvil forge bellows tongs hammer fuller swage punch chisel
bolt nut washer rivet nail screw tack brad staple anchor dowel peg pin
hinge latch catch lock padlock deadbolt hasp chain cable rope twine string
cord thread wire filament strand fiber yarn lace ribbon tape band strap
buckle clasp clip snap hook eye loop knot hitch bend splice whipping
nails kit toolbox workbench sawhorse vice grommet rivets
fire extinguisher smoke alarm carbon monoxide detector fire blanket hose
first aid kit bandage plaster gauze antiseptic ointment ointments cream
medicine pill tablet capsule syrup drops injection syringe needle vial
thermometer stethoscope blood pressure cuff otoscope reflex hammer
"""

REAL_WORDS_5000_D = """
atom molecule electron proton neutron nucleus quark lepton boson fermion
hadron baryon meson gluon photon neutrino graviton higgs antimatter
element isotope ion cation anion radical compound mixture solution solvent
solute suspension colloid emulsion alloy amalgam oxide hydroxide hydride
nitride carbide sulfide sulfate nitrate phosphate carbonate bicarbonate
chloride fluoride bromide iodide acetate citrate oxalate formate benzoate
acid base alkali alkaline salt ester ether aldehyde ketone alcohol phenol
amine amide amino peptide protein enzyme catalyst inhibitor promoter
reagent substrate product reactant equilibrium kinetics thermodynamics
enthalpy entropy gibbs freehelmholtz activation catalyst kinetics rate
order molecular atomic orbital electron cloud valence shell subshell
quantum number spin orbital angular azimuthal magnetic principal
pauli exclusion hund aufbau hunds rule heisenberg uncertainty schrodinger
planck bohr rutherford dalton thomson curie becquerel faraday avogadro
mendeleev lavoisier priestley cavendish boyle charles gaylussac
element hydrogen helium lithium beryllium boron carbon nitrogen oxygen
fluorine neon sodium magnesium aluminum silicon phosphorus sulfur chlorine
argon potassium calcium scandium titanium vanadium chromium manganese
iron cobalt nickel copper zinc gallium germanium arsenic selenium bromine
krypton rubidium strontium yttrium zirconium niobium molybdenum technetium
ruthenium rhodium palladium silver cadmium indium tin antimony tellurium
iodine xenon cesium barium lanthanum cerium praseodymium neodymium
promethium samarium europium gadolinium terbium dysprosium holmium erbium
thulium ytterbium lutetium hafnium tantalum tungsten rhenium osmium iridium
platinum gold mercury thallium lead bismuth polonium astatine radon
francium radium actinium thorium protactinium uranium neptunium plutonium
americium curium berkelium californium einsteinium fermium mendelevium
nobelium lawrencium rutherfordium dubnium seaborgium bohrium hassium
meitnerium darmstadtium roentgenium copernicium nihonium flerovium
moscovium livermorium tennessine oganesson

physics mechanics dynamics kinematics statics thermodynamics electromagnetism
optics acoustics relativity quantum cosmology astrophysics geophysics
biophysics particle nuclearparticle nuclear condensedmatter solidstate
plasma cryogenics superconductivity superfluidity magnetism electricity
voltage current resistance capacitance inductance impedance frequency
wavelength amplitude resonance interference diffraction refraction
reflection polarization dispersion scattering absorption emission
radiation convection conduction evaporation condensation sublimation
deposition ionization recombination fission fusion annihilation
annihilationpair creation redshift blueshift parsec lightyear angstrom
bohrradius plancklength plancktime planckmass planckcharge
newton joule watt pascal hertz coulomb volt ampere ohm farad henry weber
tesla siemens katal lumen lux becquerel gray sievert katal degree
kelvin celsius fahrenheit rankine
acceleration velocity displacement momentum inertia gravity gravitation
mass weight force torque angular linear centrifugal centripetal
friction tension compression shear torsion elasticity plasticity
viscosity density pressure buoyancy archimedes bernoulli venturi
turbulence laminar streamline reynolds mach speedofsound speedoflight
kinetic potential thermal chemical nuclear elastic inelastic

biology botany zoology ecology genetics evolution taxonomy anatomy
physiology cytology histology embryology microbiology mycology virology
bacteriology parasitology immunology endocrinology neurology cardiology
dermatology hematology oncology pathology pharmacology toxicology
epidemiology biochemistry molecular cellular developmental
cell membrane nucleus cytoplasm mitochondria ribosome golgi endoplasmic
reticulum lysosome peroxisome vacuole chloroplast cytoskeleton centriole
nucleolus chromatin chromosome gene allele genotype phenotype genome
dna rna mrna trna rrna codon anticodon transcription translation
replication mutation recombination crossingover meiosis mitosis
haploid diploid polyploid zygote gamete sperm egg embryo fetus
blastula gastrula larva pupa nymph metamorphosis
species genus family order class phylum kingdom domain
darwin wallace mendel lamarck linnaeus huxley pasteur koch fleming
watson crick franklin wilkins darwinian lamarckian mendelian
photosynthesis respiration fermentation glycolysis krebs calvin
atp adp nad nadp fadh coenzyme
organ system tissue organ organism population community ecosystem
biome biosphere habitat niche symbiosis mutualism commensalism
parasitism predation competition succession adaptation naturalselection
speciation extinction biodiversity conservation preservation
taxonomy cladistics phylogeny phylogenetics molecularcellular

chemistry organic inorganic physical analytical biochemistry
electrochemistry photochemistry thermochemistry radiochemistry
polymer ceramics composite crystallography spectroscopy spectrometry
chromatography titration filtration distillation extraction
precipitation crystallization sublimation centrifugation electrophoresis
microscopy electronmicroscopy fluorescence phosphorescence
nmr infrared ultraviolet visible raman xray crystallography
massspectrometry gaschromatography liquidchromatography hplc
titration burette pipette flask beaker cylinder vial cuvette
crucible mortar pestle retort condenser still alembic
ph scale buffer solution concentration molarity molality normality
mole avogadro molality molarity ppm ppb normality equivalent
polarity electronegativity dipole hydrogenbond vanderwaals covalent
ionic metallic coordinate dipoleinduced london dispersion
sigma pi bond orbital hybridization sp sp2 sp3 vsepr lewis
resonance aromatic aliphatic saturated unsaturated alkane alkene
alkyne cycloalkane benzene toluene xylene naphthalene anthracene
methane ethane propane butane pentane hexane heptane octane nonane
decane undecane dodecane methanol ethanol propanol butanol glycerol
ethylene glycol formaldehyde acetone acetic acid citric acid lactic
acid uric acid amino acid fatty acid nucleic acid

astronomy universe galaxy nebula star planet moon asteroid comet meteor
meteorite meteoroid quasar pulsar blackhole wormhole supernova
redgiant white dwarf neutron star brown dwarf mainsequence
cosmology cosmogony cosmology darkmatter darkenergy
milky way andromeda orion sagittarius scorpius cygnus lyra
telescope observatory planetarium satellite probe rover lander
mercury venus earth mars jupiter saturn uranus neptune pluto
ceres eris makemake haumea sedna
titan io europa ganymede callisto enceladus mimas titania oberon
triton charon phobos deimos
apollo artemis gemini mercury gemini voyager pioneer cassini galileo
hubble webb chandra spitzer kepler tess hubble
orbit trajectory apogee perigee perihelion aphelion equinox solstice
eclipse transit occultation conjunction opposition elongation
zodiac constellations asterism ecliptic celestial equator
geology mineral rock igneous sedimentary metamorphic
magma lava basalt granite marble slate schist gneiss quartz feldspar
mica calcite dolomite halite gypsum fluorite apatite olivine
plate tectonics continental drift pangaea gondwana laurasia
earthquake volcano tsunami fault epicenter magnitude richter mercalli
sediment erosion weathering deposition fossil fossilization
stratigraphy paleontology paleozoic mesozoic cenozoic precambrian
jurassic cretaceous triassic permian carboniferous devonian silurian
ordovician cambrian holocene pleistocene pliocene miocene oligocene
eocene paleocene
"""

REAL_WORDS_5000_E = """
program code software hardware compiler interpreter debugger linker
loader assembler disassembler bytecode opcode operand register
stack heap queue deque list array vector matrix tensor grid
tree graph trie btree rbtree avl avltree hashtable hashmap
dictionary set multiset bag tuple record struct union enum
pointer reference handle iterator generator coroutine closure
lambda function method procedure routine subroutine macro
class object instance module package namespace scope closure
inheritance polymorphism encapsulation abstraction interface
override overload virtual abstract static final const volatile
public private protected internal friend
variable constant literal identifier keyword operator
semicolon colon comma parentheses brackets braces quotes
escapesequence rawstring fstring bytes string char integer
float double decimal boolean null nil none void undefined nan
infinite precision arbitrary fixedpoint bignum
integer unsigned signed short long longlong byte word dword qword
bit nibble byte kilobyte megabyte gigabyte terabyte petabyte exabyte
zettabyte yottabyte kibibyte mebibyte gibibyte tebibyte
loop for while dowhile foreach repeat until break continue goto
branch if else elseif switch case default fallthrough
try catch finally throw raise rethrow exception error warning
assertion precondition postcondition invariant contract
parallel concurrent asynchronous synchronous blocking nonblocking
thread process fiber green thread coroutine actor
mutex semaphore monitor barrier latch atomic volatile
lock spinlock reentrant readerwriter lockfree waitfree
deadlock livelock starvation racecondition critical section
signal wait notify broadcast rendezvous mailbox channel
promise future async await yield
json xml yaml toml ini csv tsv markdown html xhtml dhtml sgml
css sass less stylus scss sass
sql nosql mongodb postgres mysql sqlite oracle redis cassandra
neo4j elasticsearch dynamodb
http https ftp sftp ssh scp telnet smtp pop3 imap ldap
dhcp dns tcp udp ip icmp arp bgp ospf rip igrp eigrp
rest soap graphql grpc rpc xmlrpc jsonrpc websocket
url uri urn endpoint path query fragment scheme host port
cookie session token jwt oauth saml openid kerberos
hash salt encryption decryption cipher plaintext ciphertext
symmetric asymmetric publickey privatekey rsa dsa ecdsa diffiehellman
aes des 3des blowfish twofish serpent rc4 rc5 chacha salsa
sha md5 crc checksum hmac mac integrity authenticity nonrepudiation
certificate authority ca x509 pem der pfx p12 pki truststore keystore
ssl tls handshake cipher suite forward secrecy perfectforwardsecrecy

python java javascript typescript c cpp csharp rust go ruby php
swift kotlin scala perl lua r julia haskell erlang elixir clojure
lisp scheme racket ocaml fsharp fortran cobol pascal delphi basic
vb vba vbscript powershell bash zsh fish csh ksh sh batch
assembly masm nasm gas llvm ir
html css javascript react angular vue svelte solid qwik
ember backbone knockout meteor
node deno bun npm yarn pnpm webpack rollup parcel vite esbuild
babel typescript flow
django flask fastapi pyramid bottle tornado
rails sinatra hanami
spring springboot micronode quarkus vertx
laravel symfony codeigniter cakephp
express koa hapi nestjs fastify
aspnet dotnetcore blazor
phoenix plug cowboy
jaxrs resteasy dropwizard
flask fastapi celery dramatiq rq
tensorflow pytorch keras jax mxnet caffe theano cntk
numpy scipy pandas matplotlib seaborn plotly bokeh altair
sklearn xgboost lightgbm catboost statsmodels
opencv pillow scikitimage mahotas simpleitk
nltk spacy gensim transformers huggingface
numpy scipy sympy networkx igraph
docker kubernetes helm kompose kustomize
terraform pulumi cloudformation ansible chef puppet salt
jenkins gitlab circleci travis actions argo tekton spinnaker
prometheus grafana datadog newrelic splunk elk
nagios zabbix sensu icinga
git mercurial subversion bazaar fossil perforce cvs
github gitlab bitbucket sourceforge azure
linux unix bsd solaris aix hpux irix
debian ubuntu fedora centos rhel arch gentoo alpine suse opensuse
redhat rocky alma mint kubuntu xubuntu lubuntu
windows macos android ios chromeos
bash zsh powershell cmd terminal console shell
sed awk grep egrep fgrep find xargs sort uniq cut paste join
tr wc head tail cat tac less more vi vim emacs nano pico ed
tar gzip bzip xz zip unzip 7z rar lz4 zstd brotli
curl wget rsync scp sftp ssh telnet netcat socat
ps top htop atop iotop iftop nethogs glances
kill pkill pgrep fg bg jobs nohup screen tmux
cron at anacron systemd init upstart sysv launchd
mount umount fdisk mkfs fsck df du lsblk blkid
lvm raid zfs btrfs ext2 ext3 ext4 xfs jfs reiserfs
iptables nftables ufw firewalld selinux apparmor
nginx apache caddy haproxy traefik envoy varnish squid
redis memcached rabbitmq kafka activemq zeromq nats pulsar
elasticsearch solr lucene sphinx opensearch
postgres mysql mariadb sqlite oracle sqlserver db2
mongodb cassandra scylla couchdb ravendb neo4j orientdb
s3 gcs azureblob minio ceph glusterfs nfs cifs smb
vpn ipsec openvpn wireguard tailscale zerotier
dns bind powerdns knot unbound coredns
loadbalancer reverse proxy gateway firewall router switch hub
cdn edge fog mist dew cloud serverless faas paas iaas saas
lambda functions azurefunctions cloudfunctions
ec2 s3 rds dynamodb sqs sns kinesis
vm virtualmachine hypervisor esxi xen kvm qemu virtualbox
vagrant packer docker podman lxc lxd
orchestration swarm mesos marathon nomad rancher
"""

REAL_WORDS_5000_F = """
apple apricot avocado banana blackberry blueberry boysenberry
cantaloupe cherry coconut cranberry currant date dragonfruit durian
elderberry fig gooseberry grape grapefruit guava honeydew huckleberry
jackfruit kiwi kumquat lemon lime lychee mandarin mango mulberry
nectarine orange papaya passionfruit peach pear persimmon pineapple
plantain plum pomegranate quince raspberry starfruit strawberry
tangelo tangerine watermelon clementine satsuma ugli yuzu bergamot
kumquat citron pomelo mandarin kaffir
artichoke asparagus avocado basil beetroot broccoli cabbage carrot
cauliflower celery chard chickpea chili cilantro collard corn cucumber
daikon dill eggplant endive fennel fenugreek garlic ginger horseradish
jicama kale kohlrabi leek lentil lettuce mustard okra onion parsley
parsnip pea peanut pepper potato pumpkin radicchio radish rhubarb
rutabaga scallion shallot spinach squash tomato turnip wasabi
watercress yam zucchini arugula bokchoy broccolini broccoflower
cabbage carrot cassava celeriac chayote chicory collards courgette
cress cucumber daikon dandelion fennel gai lan jicama kale kohlrabi
mizuna mustard napa okra parsley parsnip pea pepper purslane
radicchio radish rapini romaine rutabaga scallion sea kale shallot
sorrel spinach sprouts squash swisschard tatsoi tomatillo turnip
watercress yam zucchini
almond amaranth barley buckwheat cashew chestnut chia chickpea
coconut couscous farro flax hazelnut hemp kamut macadamia millet
oat pecan pistachio quinoa rice rye sesame sorghum spelt sunflower
tahini teff triticale walnut wheat wildrice
basil bayleaf cardamom cayenne chili chives cinnamon clove coriander
cumin curry dill fennel fenugreek galangal garlic ginger horseradish
juniper lemongrass mace marjoram mustard nutmeg oregano paprika
parsley peppercorn rosemary saffron sage savory staranise sumac
tarragon thyme turmeric vanilla zaatar
bread baguette bagel brioche ciabatta croissant focaccia naan pita
rye sourdough tortilla wrap chapati paratha roti matzo pumpernickel
marble rye wholewheat multigrain breadstick roll bun bap brioche
cookie biscuit cracker wafer macaroon macaron shortbread gingerbread
brownie blondie bar flapjack granola energybar
cake cheesecake poundcake sponge angelcake cupcake muffin scone
teacake bundt cake layer cake pancake waffle crepe blintz blini
doughnut donut beignet fritter churro funnel cake
pie tart quiche galette turnover strudel cobbler crumble crisp
pastry danish puff phyllo filo choux
pudding custard flan brulee mousse souffle parfait trifle tiramisu
cannoli profiterole eclair macaron baklava halva lokum marzipan
nougat fudge caramel toffee praline brittle taffy nougat
icecream gelato sorbet sherbet frozenyogurt semifreddo granita
chocolate truffle ganache bark candy confection lollipop gumdrop
jellybean jelly gummy marshmallow nougat licorice
sugar honey maple molasses syrup agave stevia saccharin aspartame
sucrose fructose glucose lactose maltose dextrose
salt pepper paprika cayenne chili cumin coriander cardamom
vanilla extract essence zest
coffee espresso cappuccino latte macchiato americano mocha
flatwhite cortado ristretto affogato frappe coldbrew
tea black green white oolong puer matcha sencha genmaicha
chai rooibos herbal chamomile peppermint hibiscus jasmine
juice smoothie shake frappe slushie mocktail cocktail
cola lemonade icedtea milkshake eggnog cider
wine red white rose sparkling champagne prosecco cava
beer ale lager stout porter pilsner ipa saison bock
whiskey bourbon scotch rye brandy cognac armagnac
vodka gin rum tequila mezcal sake soju baijiu
vermouth aperitif digestif liqueur amaretto kahlua baileys
cuisine french italian spanish greek portuguese german austrian
swiss belgian dutch scandinavian nordic russian polish hungarian
czech slovak romanian bulgarian serbian croatian bosnian slovenian
turkish lebanese syrian israeli palestinian egyptian moroccan
tunisian algerian libyan persian iraqi saudi yemeni omani
emirati qatari kuwaiti bahraini
indian pakistani bangladeshi srilankan nepali bhutanese
tibetan burmese thai vietnamese cambodian laotian malaysian
indonesian filipino chinese japanese korean mongolian
australian newzealand polynesian melanesian micronesian
mexican guatemalan honduran salvadoran nicaraguan costarican
panamanian colombian venezuelan ecuadorian peruvian bolivian
chilean argentine uruguayan paraguayan brazilian
cuban haitian dominican jamaican trinidadian bahamian barbadian
american cajun creole texmex soulfood southern newengland
california pacificnorthwest southwestern
sushi sashimi nigiri maki temaki uramaki onigiri donburi
ramen udon soba yakisoba okonomiyaki takoyaki yakitori
tempura tonkatsu katsucurry bento bentobox
padthai tom yum greencurry redcurry massaman panang
pho banhmi springrolls summerrolls dumpling gyoza potsticker
wonton shumai har gow baozhi xiaolongbao
kimchi bibimbap bulgogi japchae tteokbokki kimbap
naan dosa idli vada sambar rasam curry masala tandoori
biryani pulao khichdi samosa pakora chaat paneer
hummus tabbouleh falafel shawarma kebab kofta dolma
baba ganoush tahini halva baklava kofta
pizza pasta risotto gnocchi lasagna ravioli tortellini
cannelloni manicotti fettuccine linguine spaghetti penne
rigatoni fusilli farfalle orzo orecchiette cavatelli
carbonara amatriciana bolognese alfredo pesto marinara
puttanesca arrabbiata primavera vongole
paella tapas pintxos gazpacho tortilla chorizo jamon
croquettes empanada arepa pupusa tamale enchilada
quesadilla taco burrito chimichanga fajita nachos
guacamole salsa pico ceviche tostada
moussaka souvlaki gyro spanakopita dolmades horiatiki
bratwurst knockwurst weisswurst schnitzel sauerbraten
sauerbraten rouladen spatzle kartoffelsalat
coq au vin bouillabaisse cassoulet ratatouille
nicoise bourguignon confit terrine pate rillettes
fish and chips bangers mash shepherdspie cottagepie
yorkshire pudding toadinthehole bubbleandsqueak
haggis blackpudding white pudding
"""

REAL_WORDS_5000_G = """
soccer football basketball baseball softball tennis volleyball
badminton squash racquetball handball cricket rugby lacrosse
hockey icehockey fieldhockey roller hockey street hockey
golf mini golf discgolf footgolf
boxing kickboxing muaythai taekwondo karate judo aikido
jiujitsu kungfu wushu kravmaga capoeira hapkido sambo
wrestling grecoroman freestyle sumo
fencing archery shooting biathlon triathlon pentathlon decathlon
marathon ultramarathon halfmarathon sprint hurdles steeplechase
relay medley cross country track field
cycling bmx mountainbiking roadcycling track cycling cyclocross
swimming diving waterpolo synchronized swimming openwater
rowing kayaking canoeing paddleboarding surfing windsurfing
kitesurfing wakeboarding waterskiing jetskiing parasailing
sailing yachting dinghy catamaran windsurfing
skiing snowboarding crosscountry downhill slalom giant slalom
super g freestyle moguls halfpipe snowboardcross skicross
ski jumping biathlon luge bobsled skeleton curling
figure skating speed skating short track pairs dance
gymnastics artistic rhythmic trampoline tumbling acrobatics
cheerleading dance ballet jazz tap modern hiphop breakdancing
pilates yoga meditation aerobics zumba spin kickboxing
rockclimbing bouldering sportclimbing freeclimbing aidclimbing
mountaineering alpinism iceclimbing via ferrata canyoning
hiking trekking backpacking camping glamping
orienteering geocaching letterboxing
skateboarding longboarding rollerblading rollerskating
parkour freerunning tricking
basejumping skydiving paragliding hanggliding wingsuit
bungeejumping zip lining zorbing
motorsport formula1 nascar indycar rally rallycross motocross
supercross enduro trials drag racing stock car karting
equestrian dressage showjumping eventing polo polocrosse
rodeo bullriding broncriding barrelracing roping
dog racing greyhound sled racing
falconry hunting fishing fly fishing ice fishing
spearfishing bowfishing angling trawling
chess checkers draughts backgammon go shogi xiangqi
checkers mahjong dominoes dice poker bridge rummy
blackjack baccarat roulette craps slotmachine
solitaire hearts spades bridge whist euchre
cricket baseball softball rounders kickball
ultimate frisbee disc golf hacky sack footbag
paintball airsoft lasertag escape room
billiards pool snooker carom bar billiards
darts foosball air hockey shuffleboard
bowling tenpin ninepin fivepin candlepin lawn bowls
bocce petanque curling
cricket rugby aussierules gaelic american football canadian
cricket test cricket oneday twenty20 ipl
golf pga lpga rydercup majors
masters open championship pga lpga
olympics paralympics commonwealth asian panamerican
worldcup euro copa america champions
superbowl worldseries stanleycup nba finals
premier league laliga seriea bundesliga ligue1
mls nwsl nfl nba mlb nhl wnba
fifa uefa concacaf conmebol caf afc ofc
wimbledon usopen frenchopen australianopen
grandslam masters cup davis cup fed cup
formula1 motogp nascar indycar wec
tourdefrance giro vuelta parisroubaix milansanremo
bostonmarathon newyorkmarathon berlinmarathon londonmarathon
ironman kona half ironman
crossfit games toughmudder spartan race
"""

REAL_WORDS_5000_J = """
music melody harmony rhythm tempo beat meter measure bar note
pitch tone timbre dynamics articulation phrasing cadence
scale mode key signature chord arpeggio triad seventh
major minor diminished augmented suspended dominant subdominant
tonic supertonic mediant submediant leading
interval octave fifth fourth third second sixth seventh unison
sharp flat natural accidental rest slur tie staccato legato
marcato tenuto accent fermata trill mordent grace turn
genres classical baroque romantic impressionist modern contemporary
medieval renaissance rococo classical romantic postromantic
twentieth century serial atonal dodecaphonic aleatoric
minimalist postminimalist spectral electroacoustic
opera operetta oratorio cantata mass requiem motet madrigal
symphony concerto sonata suite overture prelude fugue toccata
invention rondo theme variation passacaglia chaconne
chamber quartet trio quintet sextet septet octet
string quartet piano trio wind quintet brass quintet
solo duet duo ensemble orchestra band symphony philharmonic
conductor concertmaster section principal soloist accompanist
composer arranger orchestrator transcriber
violin viola cello doublebass harp guitar lute mandolin banjo
ukulele balalaika sitar sarod veena koto shamisen pipa erhu
piano fortepiano harpsichord clavichord organ harmonium
accordion concertina bandoneon melodica
flute piccolo recorder fife ocarina panpipes
oboe englishhorn bassoon contrabassoon clarinet bassclarinet
saxophone soprano alto tenor baritone bass
trumpet cornet flugelhorn frenchhorn trombone bass trombone
tuba euphonium bugle
drum timpani bassdrum snaredrum tomtom bongo conga djembe
tabla darabuka taiko talkingdrum timbales
cymbals hihat ride crash splash china gong tamtam
triangle woodblock temple blocks claves castanets maracas
guiro cabasa shakers cowbell agogo bell
xylophone marimba glockenspiel vibraphone celesta
chimes tubular bells crotales anvil
piano keyboard synth synthesizer moog roland korg yamaha
sampler sequencer daw workstation groovebox
theremin ondes martenot trautonium telharmonium
jazz swing bebop hardbop cool jazz modal free jazz fusion
smooth jazz acid jazz nu jazz dixieland ragtime
blues delta chicago memphis piedmont texas
country bluegrass honky tonk outlaw western swing
rock classic rock hard rock progressive rock punk newwave
postpunk gothic industrial grunge alternative indie
metal heavy speed thrash death black doom power prog
pop synthpop dancepop electropop kpop jpop cpop
hiphop rap trap drill grime crunk snap
rnb soul funk disco house techno trance dubstep drumandbass
garage grime bassline jungle breakbeat trip hop downtempo
ambient newage world ethnic folk traditional
reggae dancehall ska rocksteady dub
calypso soca merengue bachata salsa cumbia tango
flamenco rumba fado sevillanas
gospel spiritual christian contemporary worship
chant gregorian byzantine coptic anglican
qawwali bhajan kirtan raga thumri ghazal
gamelan gagaku enka minyo
theater drama play stage performance act scene
comedy tragedy farce melodrama musical vaudeville
burlesque cabaret revue pantomime commedia
puppetry marionette shadow puppet
opera buffa seria verismo belcanto
ballet modern postmodern contemporary
choreography choreographer dancer troupe corps
arts painting sculpture drawing printmaking photography
ceramics pottery glasswork metalwork woodwork textiles
calligraphy illumination mosaic fresco tempera
oil acrylic watercolor gouache pastel charcoal graphite
ink wash pen brush
renaissance baroque rococo neoclassical romantic
realism naturalism impressionism postimpressionism
symbolism artnouveau artdeco fauvism expressionism
cubism futurism dada surrealism abstract expressionism
popart opart minimalism conceptualism postmodern
performance art installation video art digital art
net art bio art
museum gallery exhibition curator curator artist
critic collector patron dealer auctioneer
"""

REAL_WORDS_5000_K = """
economy economics micro macro supply demand equilibrium elasticity
inflation deflation recession depression boom bust stagflation
gdp gnp nnp nni cpi ppi pce
fiscal monetary policy taxation subsidy tariff quota embargo
sanctions austerity stimulus bailout rescue merger acquisition
bank banking central reserve federal treasury
loan mortgage credit debit overdraft interest principal
bond stock equity share dividend yield coupon maturity
bull bear market portfolio diversification asset liability
capital revenue profit loss margin markup discount
revenue expense income outgo cashflow balance sheet
asset liability equity retained earnings
audit accounting bookkeeping ledger journal trial balance
depreciation amortization accrual cash basis
invoice receipt statement voucher cheque check
wire transfer ach swift iban bic routing
creditcard debitcard atm pin chip
insurance policy premium deductible copay claim
pension annuity 401k ira roth
stock exchange nyse nasdaq lse tse hkex
commodity futures options swaps derivatives
forex currency exchange rate
bitcoin ethereum litecoin ripple dogecoin
blockchain crypto wallet mining staking
defi nft dao web3
startup entrepreneur venture capital seed round
angel investor series ipo spac
ceo cfo coo cto cio cmo chro
board chairman director shareholder stakeholder
corporation llc inc plc partnership sole proprietorship
nonprofit ngo charity foundation trust
stockholder dividend proxy merger acquisition
hostile friendly leveraged buyout

law legal justice court judge jury attorney lawyer
prosecutor defense plaintiff defendant
civil criminal constitutional administrative
tort contract property family criminal
litigation arbitration mediation negotiation settlement
appeal appellate supreme trial district circuit
statute ordinance regulation code
constitution amendment bill act
verdict sentence ruling judgment decree
plaintiff appellant appellee petitioner respondent
subpoena warrant affidavit deposition testimony
evidence exhibit witness expert
felony misdemeanor infraction violation
theft burglary robbery larceny embezzlement fraud
forgery counterfeiting perjury contempt obstruction
assault battery homicide manslaughter murder
arson vandalism trespass
custody alimony childsupport visitation
divorce annulment separation
adoption guardianship foster
will testament trust estate probate
inheritance heir beneficiary executor
trademark copyright patent trade secret
intellectual property licensing royalty
antitrust monopoly cartel collusion
gdpr hipaa sox ferpa coppa
compliance regulation oversight
government politics policy
democracy republic monarchy oligarchy
theocracy dictatorship autocracy totalitarian
authoritarian anarchist libertarian socialist
communist capitalist fascist
parliament congress senate house
president prime minister chancellor
governor mayor senator representative
election campaign candidate voter ballot
primary caucus convention
liberal conservative moderate progressive
left right centrist populist
federal state local municipal
constitution amendment bill law
executive legislative judicial
bureaucracy agency department ministry
embassy consulate ambassador diplomat
treaty alliance agreement accord
nato un eu au asean brics g7 g20 opec
sanctions embargo blockade
war peace ceasefire armistice
treaty negotiation summit
refugee immigrant emigrant migrant
asylum visa passport citizenship
naturalization deportation extradition

business commerce trade retail wholesale
manufacturing production assembly
logistics supply chain distribution
warehouse inventory stock procurement
vendor supplier distributor retailer
b2b b2c c2c d2c marketplace
ecommerce shopping cart checkout
payment gateway merchant acquirer
marketing advertising branding
campaign promotion discount coupon
seo sem ppc cpc cpm cpa roi
social media influencer content
pr public relations press release
customer client consumer buyer
satisfaction retention loyalty churn
crm erp scm wms tms
accounting payroll hr recruiting
onboarding training evaluation
promotion termination resignation retirement
salary wage hourly commission bonus
benefits insurance vacation pto
hiring firing layoff furlough
interview resume cv coverletter
reference portfolio probation
"""

REAL_WORDS_5000_L = """
accept acknowledge admit adopt advocate affirm agree aid aim allow
alter amend amplify analyze answer anticipate apologize appeal appear
apply appoint appreciate approach approve argue arrange arrive ask
assert assess assign assist assume assure attach attempt attend
attract authorize avert avoid await awaken
bake balance ban bargain bathe batter bear beat become beg begin
behave believe belong bend benefit beseech betray bid bind bite
blame blend bless blink block blot blow blush boast boil bolster
bolt bond book boost bore borrow bother bounce bow brace braid
brake branch brand breathe breed bribe bring broadcast bruise
brush bubble build bump burn burst bury buy
calculate calibrate call calm cancel capture care carry carve cast
catch cause cease celebrate censor center certify chain chair
challenge change channel charge chart chase chat cheat check cheer
chew chill chip choke choose chop claim clap clarify clash clasp
classify clean clear cleave climb cling clip cloak close cloud
clutch coach coalesce coax code coerce cohabit coil coincide
collaborate collapse collect collide colonize combine comfort
command commemorate commence commend comment commit communicate
commute compact compare compel compensate compete compile complain
complement complete complicate compliment comply compose comprehend
compress comprise compromise compute conceal concede conceive
concentrate conceptualize concern conclude concoct concur condemn
condense conduct confer confess confide configure confine confirm
confiscate conflict conform confound confront confuse congratulate
conjure connect conquer consecrate consent conserve consider
consign console consolidate conspire constitute constrain construct
consult consume contact contain contemplate contend content contest
continue contract contradict contribute contrive control convene
converge converse convert convey convict convince cook cooperate
cope copy correct correlate correspond corrode corrupt cough
counsel count counter cover covet crack crash crave crawl create
creep criticize critique croon cross crouch crowd crush cry
cultivate curb cure curl curse curve cut cycle
damage dance dangle dare darken dart dash daunt dazzle deactivate
deal debate decant decay deceive decelerate decide decipher
declare decline decode decompose decorate decouple decrease
dedicate deduce deface defame default defeat defend defer define
deflate deflect deform defraud defray defuse defy degrade
dehydrate deify delay delegate delete deliberate delight deliver
demand demean demolish demonstrate demote denote denounce dent
deny depart depend depict deplete deploy deport depose deprive
depute derail deride derive descend describe desert deserve
design designate desire despair despise destroy detach detail
detain detect deter deteriorate determine detest detonate detract
devalue devastate deviate devise devolve devote devour diagnose
dictate differentiate diffuse digest digress dilute diminish dine
dip direct disagree disappear disappoint disapprove disarm discard
discern discharge discipline disclose discolor disconnect
discontinue discourage discover discredit discuss disdain
disentangle disgrace disguise disgust dishearten disinfect
disintegrate dislike dislocate dismantle dismay dismiss disobey
dispatch dispel dispense disperse displace display displease
dispose disprove dispute disqualify disregard disrupt dissolve
dissuade distill distinguish distort distract distress distribute
distrust disturb disunite dive diverge divert divide divulge
dock dodge dominate donate doodle double doubt douse draft drag
drain dramatize draw dread dream dredge drench dress drift drill
drink drip drive drizzle droop drop drown drug drum dry dub duck
dull dumbfound dump duplicate dwell dwindle dye
earn ease eat eavesdrop ebb echo eclipse economize edge edit
educate efface effect eject elaborate elapse elect electrify
elevate elicit eliminate elongate elope elucidate elude emanate
emancipate embark embarrass embellish embezzle embody embolden
emboss embrace emerge emigrate emit emphasize employ empower
empty emulate enact encase enchant encircle enclose encompass
encounter encourage encroach encrypt endanger endorse endow
endure energize enforce engage engender engineer engrave engross
engulf enhance enjoin enlighten enlist enliven enmesh enrage
enrich enroll ensnare ensure entail entangle enter entertain
enthrall entice entitle entomb entrap entreat entrench entrust
enumerate envelop envision envy epitomize equate equip eradicate
erase erect erode erupt escalate escape escort establish esteem
estimate etch evade evaluate evaporate evict evoke evolve exact
exaggerate exalt examine exasperate excavate exceed excel except
excerpt exchange excite exclaim exclude excuse execute exemplify
exempt exercise exert exhale exhibit exhilarate exhort exhume
exonerate exorcise expand expect expedite expel expend experience
experiment expiate expire explain explode exploit explore export
expose expound express expunge extend exterminate extinguish
extol extort extract extrapolate exude exult
fabricate face facilitate fade falter familiarize fan fancy
fasten fathom fatigue favor fawn fear feast feature feign
felicitate fence ferment fertilize fester fetch feud fiddle
fight figure file fill filter finance find finish fire fish fit
fix flail flank flap flash flatten flatter flaunt flavor flee
flicker flinch flip flit float flock flood flop flourish flout
flow fluctuate flush flutter fly foam focus fold follow fool
forage forbid force forecast foresee foreshadow forestall
forfeit forge forget forgive forgo formalize forsake fortify
forward foster founder fracture fragment frame frank freeze
frequent fret frighten frolic frustrate fry fulfill fumble
fume function fund furnish further fuse fuss
gag gain gallop galvanize gamble garner gasp gather gauge gaze
generate germinate gesture get giggle give glance glare glean
glide glimmer glimpse glisten glitter glorify gloss glow glower
glut gnaw goad gobble govern grab grace graduate grant grapple
grasp grate gratify gravitate graze grease greet grieve grill
grimace grin grind grip groan groom grope grouse grovel grow
growl grumble grunt guarantee guard guess guide gulp gush
haggle hail halt halve hammer hamper hand handle hang hanker
happen harass harbor harden harm harmonize harness harrow
harvest hasten hatch hate haul haunt have hazard heal heap
hear heat heave heckle hedge heed heighten help herald herd
hesitate hide hijack hinder hinge hint hire hiss hit hoard
hoist hold holler honor hook hop hope hover howl huddle hug
hum humble humiliate hunt hurl hurry hurt hush hustle
identify idle ignite ignore illuminate illustrate imagine imbibe
imbue imitate immerse immigrate immunize impair impale impart
impeach impede impel imperil impersonate implicate implore
imply import impose impoverish impregnate impress imprint
imprison improve improvise impute inaugurate incinerate incise
incite incline include incorporate increase incriminate
incubate inculcate incur indemnify indent index indicate indict
indoctrinate induce indulge infect infer infest infiltrate
inflame inflate inflict influence inform infringe infuriate
infuse ingest inhabit inhale inherit inhibit initiate inject
injure inlay innovate inoculate inquire inscribe insert insist
inspect inspire install instigate instill institute instruct
insulate insult insure integrate intend intensify interact
intercept interchange intercede interject interlace interlock
intermingle interpret interpose interrogate intersect intersperse
intertwine intervene interview intimidate intone intoxicate
intrigue introduce intrude inundate invade inveigh invent invert
invest investigate invigorate invite invoke involve irk iron
irrigate irritate isolate issue iterate
jab jam jangle jeer jeopardize jettison jingle jolt jostle jot
judge juggle jump justify juxtapose
keep kick kindle kiss kneel knit knock knot know kowtow
label labor lace lag lament land languish lapse lash last laugh
launch launder lavish lay lead leak lean leap learn lease
lecture legalize legislate legitimize lend lengthen lessen
level levy liberate license lick lie lift lighten like limp
linger link liquefy lisp listen live load loan loathe lobby
localize locate lock lodge loiter look loom loosen loot lose
love lower lubricate lug lull lumber lure lurk
magnify mail maintain make malign malinger mandate maneuver
mangle manifest manipulate manufacture march marinate mark
maroon marshal marvel mask master match materialize matter
maul mean meander measure mediate meditate meet meld mellow
melt memorize mend mention merge mesh mesmerize migrate mime
mimic mince mind mingle minimize mint mirror misappropriate
misbehave miscalculate misdiagnose misdirect misfire misguide
mishandle misinform misinterpret misjudge mislead misplace
misprint misquote misread misrepresent miss misspell mistreat
mistrust misuse mitigate moan mobilize mock modulate moisten
mold mollify molt monitor monopolize moor motivate mount mourn
mouth move mow mumble munch murmur muster mutate mutilate
mutter
nag nail name nap narrate narrow navigate neaten necessitate
negate neglect negotiate nestle nibble niggle nip nod nominate
normalize notch notify nudge nullify numb nurture
obey object obligate oblige obliterate obscure observe obsess
obstruct obtain obtrude obviate occupy occur offend officiate
offset ogle ooze open operate opine oppose oppress optimize
orbit orchestrate ordain order organize orient originate
ornament oscillate oust outdo outgrow outlast outlive
outmaneuver outnumber outpace outperform outrun outsell
outshine outsmart outstrip outwit overcome overdo overeat
overestimate overflow overhaul overhear overheat overlap
overload overpower overrate overreach override overrule
oversee overshadow overshoot oversimplify oversleep overstate
overstay overstep overtake overthrow overturn overvalue
overwhelm overwork owe own
pace pacify pack paddle padlock paginate pain paint palliate
palpitate pamper pander paralyze pardon pare parody parry
parse partake participate partition pass paste pat patch patent
patronize pattern pave pawn pay peck pedal peek peel peep
penetrate perceive perch percolate perfect perforate perform
perfume perish permeate permit perpetuate perplex persecute
persevere persist personalize personify persuade pertain
perturb peruse pervade pervert petition petrify philosophize
photograph pick pilfer pilot pinch pine pinpoint pioneer pipe
pique pitch pity pivot placate place plagiarize plague plan
plant plaster plead pledge plow pluck plumb plummet plunk ply
poach point poise polarize police polish pollinate pollute
ponder populate pore portray pose posit position possess
postpone postulate pounce pour pout practice praise prance
prattle pray preach precede precipitate preclude predate
predict predispose predominate preen preface prefigure prefix
preheat prejudge prejudice prelude premeditate premiere
preoccupy prepare preponderate prepossess prescribe preside
press pressure presume presuppose pretend prevail prevaricate
prevent preview prey prick prickle prime primp prioritize
prise proceed proclaim procrastinate procure prod profess
proffer prognosticate program progress prohibit project
proliferate prolong promenade promulgate propel prophesy
propound proscribe prosecute prosper protect protest prove
provide provoke prowl prune pry publicize pucker puff pulsate
pulverize pummel punch puncture punish purchase purge purify
purport purvey push putrefy
quaff quail quake qualify quantify quarantine quash quaver
quell quench query quibble quicken quiet quiver quiz quote
race radiate rally ramble ramp ransack rant rap ratify ration
rationalize rattle ravage rave ravel reach react read realign
reap reappear rearrange reassemble reassert reassess reassign
rebate rebuff rebuke recalibrate recant recap recapture recede
recharge reciprocate recite reckon reclaim recline recompense
reconcile reconsider reconstruct recount recoup recreate
recruit rectify recuperate recur recycle redeem redefine
redesign redirect rediscover redistribute redouble redound
redress reek reel refashion refer refill refine reflect
refract refrain refresh refute regain regenerate regress rehash
rehearse reimburse rein reinstate reiterate rejoice rejuvenate
relapse relate relay release relegate relent relinquish relish
reload relocate remake remarry remedy reminisce remit remodel
remonstrate remunerate render renew renounce renovate reorder
reorganize repair repeal repel repent rephrase replace replay
replenish replicate reply report repose represent repress
reprimand reprint reproach reproduce reprove repudiate repulse
request require requisition rescue research resemble resent
reserve reside resign resist resolve resonate respect respire
respond rest restart restate restore restrain restrict
restructure result resurrect retain retaliate retard reteach
retire retort retract retreat retrieve return reunite reveal
revel revenge reverberate revere reverse revert review revile
revise revive revoke revolt revolutionize revolve reward rhyme
ride ridicule ring rinse riot ripen ripple rise risk rival
rivet roam roar roast rob rock roll romp rotate rouse rove rub
ruffle ruin rule ruminate rummage run rupture rush rustle
sabotage sadden saddle safeguard sail salivate sally salute
sanctify sanction sanitize sap sashay satiate satirize satisfy
saturate saunter save savor say scald scale scamper scan
scandalize scar scare scavenge scatter scold scoop scoot scorch
score scorn scour scout scowl scramble scrap scrape scratch
scrawl scream screen screw scribble scrimp scroll scrounge
scrub scrutinize scuff sculpt scurry seal search season seat
secede seclude secrete secure sedate seduce seep seethe
segregate seize select sell send sense separate sequester
serenade serve set settle sever sew shackle shake shame shape
share sharpen shatter shave shear sheathe shed shelter shelve
shepherd shield shift shine ship shirk shiver shock shoot shop
shore shorten shout shove shovel show shred shriek shrink
shroud shrug shuck shudder shuffle shun shunt shut shutter
sicken sidestep sift sigh sight signify silence simmer simplify
simulate sing singe sink sip situate sketch skew skid skim
skimp skirmish skulk slack slam slander slant slash slate
slaughter slay sled sleep slice slide slight sling slink slip
slit slither slog slosh slouch slow slug slumber slump smack
smash smear smell smite smile smolder smoke smother smudge
smuggle snag snap snarl snatch sneak sneer sniff snip snooze
snore snort snub snuff soak soar sober socialize soften solder
solicit solidify solve soothe sort sough sow span spark sparkle
spatter spawn speak specialize specify speckle speculate spew
spike spill spin spiral spit splash splay splice splinter
split spoil sponsor spook spool spout sprain sprawl spray
spread sprig sprinkle sprint sprout spruce spur spurn sputter
spy squabble squander squat squawk squeak squeal squelch
squint squirm squirt stab stabilize stack stagger stagnate
stain stammer stamp stampede stand standardize stare start
startle starve stash stave stay steady steal steam steep
steer stem stencil step stereotype sterilize stick stifle
stimulate sting stipulate stir stitch stock stoke stomp stoop
stop store storm stow straddle straggle straighten strain
strangle strategize stray streak stream strengthen stress
stretch strew stride strike string strip strive stroke stroll
structure struggle strut stub study stuff stumble stun stupefy
stutter style subdue submerge subordinate submit subscribe
subside subsidize subsist substantiate substitute subsume
subtract subvert succeed succor succumb suck suffice suffocate
suggest suit sulk sully summarize summon sup supercharge
supersede supervise supplant supplement supplicate supply
support suppose suppress surge surmise surmount surpass
surrender surround survey survive suspect suspend sustain
swallow swamp swat sway swear sweat sweep sweeten swell
swelter swerve swindle swing swirl swoop symbolize sympathize
synchronize syndicate synthesize systematize
tabulate tackle tag tail tailor taint take talk tally tame
tamper tang tangle tarnish tarry taste tattle taunt teach tear
tease telegraph telephone televise tell temper tempt tender
terminate terrify test testify thank thaw think thirst thrash
threaten thrill thrive throb throng throw thrust thwart tickle
tidy tie tighten tilt tinker tint tip tire tolerate toil toll
toot topple torment torture toss totter touch toughen tout tow
tower toy trace track trade trail train trample transact
transcend transcribe transfer transgress transmit transmute
transpire transplant transpose travel traverse travesty tread
treasure treat treble tremble trench trespass trick trickle
trifle trigger trim triple trivialize triumph trot trouble
trounce trudge trump truncate trust try tuck tug tumble tune
tunnel turn tussle tutor tweak twinkle twirl twist twitch type
typify tyrannize
unarm unbend unbind unbolt unburden unbutton uncap unchain
unclasp uncoil uncover uncross undress undulate unfasten unfold
unfurl unhinge unify unite unlace unleash unload unlock unmask
unpack unplug unravel unroll unseat unsettle untangle untie
unveil unwind unwrap upbraid update upend uphold upgrade
upholster uproot upset urge usher usurp utilize utter
vacate vacillate validate valorize value vandalize vanish
vanquish vaporize vary vault veer vend veneer venerate venture
verbalize verify vex vibrate victimize vie vilify vindicate
violate visit visualize vitiate vivify vocalize voice volunteer
vote vouch vouchsafe vow voyage vulgarize
wade waffle waft wag wage wager wail wait waive wake walk
wallow waltz wander wane want warble ward warm warn warp
warrant wash waste watch water wave waver wax waylay weaken
wean wear weary weather weave wed wedge weed weep weigh weld
welcome welter wend whack wheedle wheel wheeze whet whimper
whine whirl whisk whisper whistle whiten whittle widen wield
wiggle wilt win wince wind wink winnow wipe wire wither
withhold withstand wobble woo work worry worship wound
wrangle wrap wreak wreck wrench wrest wrestle wriggle wring
wrinkle write writhe
yank yawn yearn yell yield yodel
zap zero zip zoom
"""

print(f"Embedded batches: A, B, C, D, E, F, G, J, K, L "
      f"({sum(len(b.split()) for b in [REAL_WORDS_5000, REAL_WORDS_5000_B, REAL_WORDS_5000_C, REAL_WORDS_5000_D, REAL_WORDS_5000_E, REAL_WORDS_5000_F, REAL_WORDS_5000_G, REAL_WORDS_5000_J, REAL_WORDS_5000_K, REAL_WORDS_5000_L]):,} tokens)")

# ==================================================================
# ★ LOAD EXTERNAL BATCHES H, I from ./word_batches/batch_X.txt
# ==================================================================
WORD_BATCH_DIR = "word_batches"
# C, D, E, F, G, J, K, L are now EMBEDDED. Only H and I are loaded from disk.
EXTERNAL_BATCH_LETTERS = ["H", "I"]

def _load_external_batches():
    """Load word_batches/batch_H.txt, batch_I.txt if present."""
    loaded = {}
    if not os.path.isdir(WORD_BATCH_DIR):
        return loaded
    for letter in EXTERNAL_BATCH_LETTERS:
        path = os.path.join(WORD_BATCH_DIR, f"batch_{letter}.txt")
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                loaded[letter] = f.read()
            print(f"  Loaded word batch {letter}: {path}")
        except Exception as e:
            print(f"  Failed to load {path}: {e}")
    return loaded

_EXTERNAL = _load_external_batches()

# ---- Build the tuple of ALL embedded + external batches ----
ALL_REAL_WORD_BATCHES = [
    REAL_WORDS_5000,      # A
    REAL_WORDS_5000_B,    # B
    REAL_WORDS_5000_C,    # C
    REAL_WORDS_5000_D,    # D
    REAL_WORDS_5000_E,    # E
    REAL_WORDS_5000_F,    # F
    REAL_WORDS_5000_G,    # G
    REAL_WORDS_5000_J,    # J
    REAL_WORDS_5000_K,    # K
    REAL_WORDS_5000_L,    # L
]
for _letter in EXTERNAL_BATCH_LETTERS:
    if _letter in _EXTERNAL:
        ALL_REAL_WORD_BATCHES.append(_EXTERNAL[_letter])
ALL_REAL_WORD_BATCHES = tuple(ALL_REAL_WORD_BATCHES)

print(f"Word batches available: {len(ALL_REAL_WORD_BATCHES)} "
      f"(A-L embedded; {len(_EXTERNAL)} external)")

# ==================================================================
# Dictionary builder
# ==================================================================
def download_12_dictionaries():
    if not os.path.exists(DICT_DIR):
        try: os.makedirs(DICT_DIR)
        except Exception: pass
    all_words = set(); success = 0
    for filename, url in zip(DICTIONARY_FILES, DICTIONARY_URLS):
        local_path = os.path.join(DICT_DIR, filename)
        print(f"  Downloading {filename} ...")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=20) as response:
                content = response.read()
            if b'<html' in content[:200].lower():
                print(f"    WARNING: HTML. Skip."); continue
            with open(local_path, 'wb') as f: f.write(content)
            text = content.decode('utf-8', errors='ignore')
            for line in text.splitlines():
                w = line.strip()
                if not w: continue
                try:
                    decoded = base64.b64decode(w, validate=True).decode('utf-8')
                    all_words.add(decoded)
                except Exception:
                    all_words.add(w)
            print(f"    OK ({len(content)} bytes)")
            success += 1
        except Exception as e:
            print(f"    FAIL: {e}")
    print(f"  Downloaded {success}/12 → {len(all_words):,} words")
    return all_words

def build_real_dictionary(try_download=True):
    words = set()
    if try_download:
        print("\nStep 1: 12 Google Drive dictionary files")
        try:
            words |= download_12_dictionaries()
            print(f"  Running total: {len(words):,}")
        except Exception as e:
            print(f"  Download error (ignored): {e}")

    print("\nStep 2: System dictionaries")
    for path in ["/usr/share/dict/words", "/usr/share/dict/american-english",
                 "/usr/share/dict/british-english", "/usr/share/hunspell/en_US.dic",
                 os.path.expanduser("~/.local/share/dict/words")]:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        w = line.split('/')[0].strip().lower()
                        if w and w.isalpha() and 1 <= len(w) <= 64:
                            words.add(w)
                print(f"  {path}: total {len(words):,}")
            except Exception as e:
                print(f"  Skip {path}: {e}")

    print("\nStep 3: english-words pip package")
    try:
        from english_words import get_english_words_set
        extra = {w.lower() for w in get_english_words_set(['web2', 'gcide'], lower=True)
                 if w.isalpha() and len(w) <= 64}
        words |= extra
        print(f"  Total: {len(words):,}")
    except ImportError:
        print("  Not installed")
    except Exception as e:
        print(f"  Failed: {e}")

    print("\nStep 4: NLTK WordNet")
    try:
        from nltk.corpus import words as nltk_words
        extra = {w.lower() for w in nltk_words.words() if w.isalpha() and len(w) <= 64}
        words |= extra
        print(f"  Total: {len(words):,}")
    except Exception:
        print("  Not available")

    print(f"\nStep 4b: Built-in REAL_WORDS batches ({len(ALL_REAL_WORD_BATCHES)} blobs) — always on")
    real_extra = set()
    for blob in ALL_REAL_WORD_BATCHES:
        real_extra |= {w.lower() for w in blob.split() if w.isalpha() and 1 <= len(w) <= 64}
    before = len(words)
    words |= real_extra
    print(f"  Added {len(real_extra):,} hard-coded words "
          f"({len(words) - before:,} new). Total: {len(words):,}")

    if len(words) < 100:
        print("\nStep 5: AI-generated fallback (minimal)")
        words |= _build_ai_dictionary()

    words = sorted(w for w in words if w and w.isascii() and 1 <= len(w) <= 64)
    print(f"\nFINAL dictionary: {len(words):,} words")
    return words

def _build_ai_dictionary():
    BASE = """the be to of and a in that have i it for not on with he as you do at this
    but his by from they we say her she or an will my one all would there their what
    data file code program computer system network server client software hardware
    internet website email message password user account login database algorithm
    function variable constant array list queue stack tree graph node compress
    decompress encode decode encrypt decrypt hash checksum verify lossless test
    build compile run execute debug error bug crash fix patch update version
    document folder directory path link address url http https protocol port socket
    bit byte word block stream buffer cache memory disk drive cpu gpu ram rom
    python java cpp c rust go ruby php swift kotlin scala perl lua
    lorem ipsum dolor sit amet consectetur adipiscing elit sed eiusmod tempor
    incididunt labore dolore magna aliqua enim minim veniam quis nostrud exercitation
    ullamco laboris nisi aliquip commodo consequat duis aute irure reprehenderit
    voluptate velit esse cillum fugiat nulla pariatur excepteur occaecat cupidatat
    proident sunt culpa officia deserunt mollit anim laborum""".split()
    PREFIXES = ["un","re","pre","dis","non","anti","over","under","multi","inter",
                "trans","auto","micro","macro","bio","eco","neuro","techno","cyber",
                "nano","astro","hydro","thermo","meta","proto","pseudo","quasi"]
    SUFFIXES = ["ing","ed","er","est","ly","tion","ment","ness","ful","less","able",
                "ible","ous","ive","al","ic","ity","ize","ance","ence","ate","ify",
                "ship","hood","ward","wise","ist","ism","ology","ography","scope",
                "graph","gram","logy","nomy","pathy"]
    words = set(BASE)
    for w in BASE:
        if len(w) >= 3:
            for sfx in ["s","es","ed","ing","er","est","ly"]: words.add(w + sfx)
    for p in PREFIXES:
        for w in BASE:
            if len(w) >= 3:
                words.add(p + w); words.add(p + w + "ed"); words.add(p + w + "ing")
    for w in BASE:
        for s in SUFFIXES:
            if len(w) >= 3: words.add(w + s)
    for n in ["zero","one","two","three","four","five","six","seven","eight",
              "nine","ten","eleven","twelve","twenty","thirty","forty","fifty",
              "hundred","thousand","million","billion"]:
        words.add(n); words.add(n + "th")
    for blob in ALL_REAL_WORD_BATCHES:
        words |= {w.lower() for w in blob.split() if w.isalpha() and 1 <= len(w) <= 64}
    return words

# ============================ CONSTANTS ============================
PRIMES = [p for p in range(2, 256) if all(p % d != 0 for d in range(2, int(p ** 0.5) + 1))]
PI_DIGITS = [79, 17, 111]

def find_nearest_prime_around(n):
    if n < 2: return 2
    o = 0
    while True:
        c1, c2 = n - o, n + o
        if c1 >= 2 and all(c1 % d != 0 for d in range(2, int(c1 ** 0.5) + 1)): return c1
        if c2 >= 2 and all(c2 % d != 0 for d in range(2, int(c2 ** 0.5) + 1)): return c2
        o += 1

_CONST_DIAPASON_ITER_CODE = [
    (2, 0b10), (2, 0b11), (3, 0b010), (3, 0b011), (4, 0b0010), (4, 0b0011),
    (5, 0b00010), (5, 0b00011), (6, 0b000010), (6, 0b000011), (7, 0b0000010),
    (7, 0b0000011), (8, 0b00000010), (8, 0b00000011), (9, 0b000000010),
    (9, 0b000000011),
]
_CONST_DIAPASON_ITER_DECODE = {v: k for k, v in enumerate(_CONST_DIAPASON_ITER_CODE)}

ALPHABET_6BIT = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 \n"
CHAR_TO_6BIT = {ch: i for i, ch in enumerate(ALPHABET_6BIT)}
SIXBIT_TO_CHAR = {i: ch for ch, i in CHAR_TO_6BIT.items()}

PAQ_STATE_TABLE = [
    [1,2,0,0],[3,5,0,1],[4,6,2,0],[7,10,0,2],[8,12,3,0],[9,13,1,1],[11,14,0,3],
    [15,19,4,0],[16,23,2,1],[17,24,2,1],[18,25,2,1],[20,27,1,2],[21,28,1,2],
    [22,29,1,2],[26,30,0,4],[31,33,5,0],[32,34,3,1],[35,37,1,3],[36,38,1,3],
    [39,42,0,5],[40,43,4,1],[41,44,2,2],[45,48,1,4],[46,49,1,4],[47,50,1,4],
    [51,52,0,6],[53,55,6,0],[54,56,4,1],[57,59,2,3],[58,60,2,3],[61,63,0,7],
    [62,64,5,1],[65,66,3,2],[67,69,1,5],[68,70,1,5],[71,73,0,8],[72,74,6,1],
    [75,76,4,2],[77,78,2,4],[79,80,2,4],[81,82,0,9],[83,84,7,1],[85,86,5,2],
    [87,88,3,3],[89,90,1,6],[91,92,0,10],[93,94,8,1],[95,96,6,2],[97,98,4,3],
    [99,100,2,5],[101,102,0,11],[103,104,9,1],[105,106,7,2],[107,108,5,3],
    [109,110,3,4],[111,112,1,7],[113,114,0,12],[115,116,10,1],[117,118,8,2],
    [119,120,6,3],[121,122,4,4],[123,124,2,6],[125,126,0,13],[127,128,11,1],
    [129,130,9,2],[131,132,7,3],[133,134,5,4],[135,136,3,5],[137,138,1,8],
    [139,140,0,14],[141,142,12,1],[143,144,10,2],[145,146,8,3],[147,148,6,4],
    [149,150,4,5],[151,152,2,7],[153,154,0,15],[155,156,13,1],[157,158,11,2],
    [159,160,9,3],[161,162,7,4],[163,164,5,5],[165,166,3,6],[167,168,1,9],
    [169,170,0,16],[171,172,14,1],[173,174,12,2],[175,176,10,3],[177,178,8,4],
    [179,180,6,5],[181,182,4,6],[183,184,2,8],[185,186,0,17],[187,188,15,1],
    [189,190,13,2],[191,192,11,3],[193,194,9,4],[195,196,7,5],[197,198,5,6],
    [199,200,3,7],[201,202,1,10],[203,204,0,18],[205,206,16,1],[207,208,14,2],
    [209,210,12,3],[211,212,10,4],[213,214,8,5],[215,216,6,6],[217,218,4,7],
    [219,220,2,9],[221,222,0,19],[223,224,17,1],[225,226,15,2],[227,228,13,3],
    [229,230,11,4],[231,232,9,5],[233,234,7,6],[235,236,5,7],[237,238,3,8],
    [239,240,1,11],[241,242,0,20],[243,244,18,1],[245,246,16,2],[247,248,14,3],
    [249,250,12,4],[251,252,10,5],[253,254,8,6],[255,255,6,7],
]

class TransformError(Exception): pass
class DecompressionError(Exception): pass
class IntegrityError(Exception): pass

def mod_inv(a, m):
    if a == 0: return None
    m0 = m; y = 0; x = 1
    if m == 1: return 0
    while a > 1:
        q = a // m; t = m; m = a % m; a = t
        t = y; y = x - q * y; x = t
    if x < 0: x += m0
    return x

MAGIC = b'PJP4'
MAGIC_LEN = 4
HASH_LEN = 32
HEADER_LEN = MAGIC_LEN + HASH_LEN

# ============================ COMPRESSOR ============================
class UnifiedCompressor:
    ULTRA_TIME_LIMIT = 300
    QUANTUM_QUBITS = 8
    WINDOW_SIZE = 2048
    MIN_MATCH = 3
    MAX_MATCH = 2048
    MAX_DIST = 2048

    def __init__(self, try_download=True):
        print("\n" + "=" * 60)
        print("BUILDING DICTIONARY")
        print("=" * 60)
        words = build_real_dictionary(try_download=try_download)
        self.static_dict = words
        self.word_to_index = {w: i for i, w in enumerate(words)}

        self.PI_DIGITS = PI_DIGITS.copy()
        self.seed_tables = self._gen_seed_tables()
        self.fibonacci = self._gen_fib(100)
        self.PI_STR = "3.14159265358979323846264338327950288419716939937510"
        self.repeat_count = 100
        self.mod_state_table = [[(v - 400) & 0xFF for v in row] for row in PAQ_STATE_TABLE]
        self._build_mask_46()
        self._build_transform_maps()
        if USE_QUANTUM and HAS_QISKIT:
            self._precompute_quantum_transforms()

    # ---------- helpers ----------
    def _build_mask_46(self):
        base = [1, 2, 4, 8, 16, 32, 64, 128, 3, 6]
        self.mask_46 = [(b - 10) & 0xFF for b in base] * 10
    def _gen_seed_tables(self, num=126, size=40, seed=42):
        random.seed(seed)
        return [[random.randint(5, 255) for _ in range(size)] for _ in range(num)]
    def _gen_fib(self, n):
        a, b = 0, 1; res = [a, b]
        for _ in range(2, n): a, b = b, a + b; res.append(b)
        return res
    def get_seed(self, idx, val):
        return self.seed_tables[idx][val % 40] if 0 <= idx < len(self.seed_tables) else 0
    def _append_bits(self, bl, v, c):
        for i in range(c - 1, -1, -1): bl.append((v >> i) & 1)
    def _read_bits(self, bits, pos, cnt):
        v = 0
        for i in range(cnt):
            if pos + i >= len(bits): return 0
            v = (v << 1) | bits[pos + i]
        return v
    def _get_pattern(self, size, index):
        random.seed(12345 + size * 100 + index)
        return [random.randint(0, 255) for _ in range(size)]
    def _calculate_repeats(self, data):
        if not data: return 1
        L = len(data); s = sum(data) % 256
        return max(1, min(256, ((L * 13 + s * 17) % 256) + 1))
    def _verify_lossless(self, orig, trans, rev):
        try: return rev(trans) == orig
        except Exception: return False

    # ---------------- Transform 00 ----------------
    def transform_00(self, data):
        if not data: return struct.pack('>I', 0)
        br, bl, bsh = None, float('inf'), []
        cur = bytearray(data); ap = []; orig = bytes(data)
        for _ in range(10):
            bs = 0; bsh_ = cur; bsc = float('-inf')
            for sh in range(256):
                tmp = bytearray(cur)
                for j in range(len(tmp)): tmp[j] = (tmp[j] + sh) % 256
                sc = 0; i = 0
                while i < len(tmp):
                    val = tmp[i]; run = 1; i += 1
                    while i < len(tmp) and tmp[i] == val: run += 1; i += 1
                    sc += run * run
                if sc > bsc: bsc = sc; bsh_ = tmp; bs = sh
            ap.append(bs)
            rle = self._apply_rle(bsh_, bs)
            dec = self._rle_decode(rle)
            if dec is not None:
                test = bytearray(dec)
                for s in ap:
                    for j in range(len(test)): test[j] = (test[j] - s) % 256
                if bytes(test) == orig and len(rle) < bl:
                    bl = len(rle); br = rle; bsh = ap.copy()
            cur = bsh_
            if len(rle) >= len(data): break
        if br is None or bl >= len(data):
            return struct.pack('>I', len(data)) + bytes([0]) + data
        h = bytearray(struct.pack('>I', len(data)))
        h.append(len(bsh)); h.extend(bsh)
        return bytes(h) + br

    def _apply_rle(self, sd, shift):
        bits = []
        self._append_bits(bits, 0b010, 3); self._append_bits(bits, shift, 8)
        i = 0; n = len               (sd)
        while i < n:
            val = sd[i]; run = 1; i += 1
            while i < n and sd[i] == val: run += 1; i += 1
            while run >= 13:
                ch = min(run, 268)
                self._append_bits(bits, 0b1111, 4)
                self._append_bits(bits, ch - 13, 8); self._append_bits(bits, val, 8)
                run -= ch
            if run == 1:
                self._append_bits(bits, 0b00, 2); self._append_bits(bits, val, 8)
            elif run <= 5:
                self._append_bits(bits, 0b01, 2)
                self._append_bits(bits, run - 2, 2); self._append_bits(bits, val, 8)
            elif run <= 12:
                self._append_bits(bits, 0b10, 2)
 self._append_bits(bits, run - 6, 3); self._append_bits(bits, val, 8)
        pad = (8 - len(bits) % 8) % 8; self._append_bits(bits, 0, pad)
        out = bytearray()
        for j in range(0, len(bits), 8):
            b = 0
            for k in range(8):
                if j + k < len(bits): b = (b << 1) | bits[j + k]
            out.append(b)
        return bytes(out)

    def reverse_transform_00(self, cdata):
        if not cdata or cdata == struct.pack('>I', 0): return b''
        if len(cdata) < 4: raise TransformError("RLE short")
        ol = struct.unpack('>I', cdata[:4])[0]; cdata = cdata[4:]
        if not cdata: return b''
        if cdata[0] == 0: return cdata[1:ol + 1]
        np = cdata[0]
        if np == 0 or len(cdata) < 1 + np: raise TransformError("RLE hdr")
        shifts = list(cdata[1:1 + np]); rle = cdata[1 + np:]
        dec = self._rle_decode(rle)
        if dec is None: raise TransformError("RLE dec")
        cur = bytearray(dec[:ol])
        for sh in reversed(shifts):
            for i in range(len(cur)): cur[i] = (cur[i] - sh) % 256
        return bytes(cur)

    def _rle_decode(self, data):
        if not data: return None
        bits = []
        for b in data:
            for i in range(7, -1, -1): bits.append((b >> i) & 1)
        pos = 0; nb = len(bits)
        if nb < 11: return None
        if self._read_bits(bits, pos, 3) != 0b010: return None
        pos += 3 + 8
        out = bytearray()
        while pos < nb:
            if pos + 2 > nb: break
            pfx = self._read_bits(bits, pos, 2); pos += 2
            if pfx == 0b00:
                if pos + 8 > nb: break
                run = 1
            elif pfx == 0b01:
                if pos + 2 + 8 > nb: break
                run = 2 + self._read_bits(bits, pos, 2); pos += 2
            elif pfx == 0b10:
                if pos + 3 + 8 > nb: break
                run = 6 + self._read_bits(bits, pos, 3); pos += 3
            else:
                if pos + 2 + 8 + 8 > nb: break
                if self._read_bits(bits, pos, 2) != 0b11: return None
                pos += 2
                run = 13 + self._read_bits(bits, pos, 8); pos += 8
            if pos + 8 > nb: break
            val = self._read_bits(bits, pos, 8); pos += 8
            out.extend([val] * run)
        for i in range(pos, nb):
            if bits[i] != 0: return None
        return out

    # ---------------- Transforms 01-21 ----------------
    def transform_01(self, d):
        t = bytearray(d); r = self.repeat_count
        for prime in PRIMES:
            xv = prime if prime == 2 else max(1, math.ceil(prime * 4096 / 28672))
            for _ in range(r):
                for i in range(0, len(t), 3):
                    if i < len(t): t[i] ^= xv
        return bytes(t)
    reverse_transform_01 = transform_01

    def transform_02(self, d):
        if not d: return b'\x00'
        t = bytearray(d); pi = (len(d) + sum(d)) % 256
        pv = self._get_pattern(4, pi)
        for i in range(1, len(t), 4):
            if i < len(t): t[i] ^= pv[i % len(pv)]
        return bytes([pi]) + bytes(t)
    def reverse_transform_02(self, d):
        if d == b'\x00': return b''
        if len(d) < 2: raise TransformError("T02")
        pi = d[0]; t = bytearray(d[1:]); pv = self._get_pattern(4, pi)
        for i in range(1, len(t), 4):
            if i < len(t): t[i] ^= pv[i % len(pv)]
        return bytes(t)

    def transform_03(self, d):
        if not d: return b'\x00'
        t = bytearray(d); rot = (len(d) * 13 + sum(d)) % 8
        if rot == 0: rot = 1
        for i in range(2, len(t), 5):
            if i < len(t): t[i] = ((t[i] << rot) | (t[i] >> (8 - rot))) & 0xFF
        return bytes([rot]) + bytes(t)
    def reverse_transform_03(self, d):
        if d == b'\x00': return b''
        if len(d) < 2: raise TransformError("T03")
        rot = d[0]; t = bytearray(d[1:])
        for i in range(2, len(t), 5):
            if i < len(t): t[i] = ((t[i] >> rot) | (t[i] << (8 - rot))) & 0xFF
        return bytes(t)

    def transform_04(self, d):
        t = bytearray(d)
        for _ in range(self.repeat_count):
            for i in range(len(t)): t[i] = (t[i] - (i % 256)) % 256
        return bytes(t)
    def reverse_transform_04(self, d):
        t = bytearray(d)
        for _ in range(self.repeat_count):
            for i in range(len(t)): t[i] = (t[i] + (i % 256)) % 256
        return bytes(t)

    def transform_05(self, d, s=3):
        return bytes(((b << s) | (b >> (8 - s))) & 0xFF for b in d)
    def reverse_transform_05(self, d, s=3):
        return bytes(((b >> s) | (b << (8 - s))) & 0xFF for b in d)

    def transform_06(self, d, sd=42):
        random.seed(sd); sub = list(range(256)); random.shuffle(sub)
        return bytes(sub[b] for b in d)
    def reverse_transform_06(self, d, sd=42):
        random.seed(sd); sub = list(range(256)); random.shuffle(sub)
        inv = [0] * 256
        for i in range(256): inv[sub[i]] = i
        return bytes(inv[b] for b in d)

    def transform_07(self, d):
        t = bytearray(d); r = self.repeat_count
        sh = len(d) % len(self.PI_DIGITS)
        pr = self.PI_DIGITS[sh:] + self.PI_DIGITS[:sh]
        sz = len(d) % 256
        for i in range(len(t)): t[i] ^= sz
        for _ in range(r):
            for i in range(len(t)): t[i] ^= pr[i % len(pr)]
        return bytes(t)
    reverse_transform_07 = transform_07

    def transform_08(self, d):
        t = bytearray(d); r = self.repeat_count
        sh = len(d) % len(self.PI_DIGITS)
        pr = self.PI_DIGITS[sh:] + self.PI_DIGITS[:sh]
        p = find_nearest_prime_around(len(d) % 256)
        for i in range(len(t)): t[i] ^= p
        for _ in range(r):
            for i in range(len(t)): t[i] ^= pr[i % len(pr)]
        return bytes(t)
    reverse_transform_08 = transform_08

    def transform_09(self, d):
        t = bytearray(d); r = self.repeat_count
        sh = len(d) % len(self.PI_DIGITS)
        pr = self.PI_DIGITS[sh:] + self.PI_DIGITS[:sh]
        p = find_nearest_prime_around(len(d) % 256)
        sd = self.get_seed(len(d) % len(self.seed_tables), len(d))
        for i in range(len(t)): t[i] ^= p ^ sd
        for _ in range(r):
            for i in range(len(t)): t[i] ^= pr[i % len(pr)] ^ (i % 256)
        return bytes(t)
    reverse_transform_09 = transform_09

    def transform_10(self, data):
        if not data: return b'\x00'
        cnt = sum(1 for i in range(len(data) - 1) if data[i:i + 2] == b'X1')
        n = (((cnt * 2) + 1) // 3) * 3 % 256
        t = bytearray(data)
        for i in range(len(t)): t[i] ^= n
        return bytes([n]) + bytes(t)
    def reverse_transform_10(self, data):
        if len(data) < 1: raise TransformError("T10")
        n = data[0]; t = bytearray(data[1:])
        for i in range(len(t)): t[i] ^= n
        return bytes(t)

    def transform_11(self, data):
        if not data: return b''
        t = bytearray(data); L = len(t)
        for i in range(L):
            fi = (i + L) % len(self.fibonacci)
            fv = self.fibonacci[fi] % 256
            pv = (i * 13 + L * 17) % 256
            t[i] ^= (fv ^ pv) % 256
        return bytes(t)
    reverse_transform_11 = transform_11

    def transform_12(self, data):
        t = bytearray(data)
        for i in range(len(t)): t[i] ^= self.fibonacci[i % len(self.fibonacci)] % 256
        return bytes(t)
    reverse_transform_12 = transform_12

    def transform_13(self, d):
        if not d: return b'\x00'
        r = self._calculate_repeats(d); cv = len(d) % 256; pv = []
        for _ in range(r): cv = find_nearest_prime_around(cv); pv.append(cv)
        t = bytearray(d); xv = pv[-1] if pv else 0
        for i in range(len(t)): t[i] ^= xv
        return bytes([(r - 1) % 256]) + bytes(t)
    def reverse_transform_13(self, d):
        if d == b'\x00': return b''
        if len(d) < 2: raise TransformError("T13")
        r = (d[0] + 1) % 256
        if r == 0: r = 256
        t = bytearray(d[1:]); cv = len(t) % 256; pv = []
        for _ in range(r): cv = find_nearest_prime_around(cv); pv.append(cv)
        xv = pv[-1] if pv else 0
        for i in range(len(t)): t[i] ^= xv
        return bytes(t)

    def transform_14(self, d):
        if not d: return b'\x00'
        return d + bytes([sum(d) % 256])
    def reverse_transform_14(self, d):
        if not d: raise TransformError("T14")
        return d[:-1]

    def transform_15(self, d):
        if not d: return b'\x00'
        t = bytearray(d); pi = len(d) % 256
        pv = self._get_pattern(3, pi)
        for i in range(0, len(t), 3):
            if i < len(t): t[i] = (t[i] + pv[i % len(pv)]) % 256
        return bytes([pi]) + bytes(t)
    def reverse_transform_15(self, d):
        if d == b'\x00': return b''
        if len(d) < 2: raise TransformError("T15")
        pi = d[0]; t = bytearray(d[1:]); pv = self._get_pattern(3, pi)
        for i in range(0, len(t), 3):
            if i < len(t): t[i] = (t[i] - pv[i % len(pv)]) % 256
        return bytes(t)

    def transform_16(self, data):
        if not data: return b''
        xv = (len(data) * 7 + 13) % 256
        return bytes(b ^ xv for b in data)
    reverse_transform_16 = transform_16

    def transform_17(self, data):
        if not data: return b''
        mask = bytes([0x24, 0x3F, 0x6A, 0x88])
        t = bytearray(data)
        for i in range(len(t)): t[i] ^= mask[i % len(mask)]
        return bytes(t)
    reverse_transform_17 = transform_17

    def transform_18(self, data):
        if not data: return b''
        decimal.getcontext().prec = 60
        pi = decimal.Decimal("3.14159265358979323846264338327950288419716939937510")
        basel = (pi * pi) / decimal.Decimal(6)
        s = str(basel).replace('.', '')[:max(10, len(data) // 2 + 5)]
        mask = bytes(int(s[i:i + 2]) % 256 for i in range(0, len(s), 2))
        t = bytearray(data)
        for i in range(len(t)): t[i] ^= mask[i % len(mask)]
        return bytes(t)
    def reverse_transform_18(self, data):
        if not data: return b''
        decimal.getcontext().prec = 60
        pi = decimal.Decimal("3.14159265358979323846264338327950288419716939937510")
        basel = (pi * pi) / decimal.Decimal(6)
        s = str(basel).replace('.', '')[:max(10, len(data) // 2 + 5)]
        mask = bytes(int(s[i:i + 2]) % 256 for i in range(0, len(s), 2))
        t = bytearray(data)
        for i in range(len(t)): t[i] ^= mask[i % len(mask)]
        return bytes(t)

    def transform_19(self, data):
        if not data: return b''
        decimal.getcontext().prec = 60
        e = decimal.Decimal(1).exp(); five_e = decimal.Decimal(5) * e
        s = str(five_e).replace('.', '')[:max(10, len(data) // 2 + 5)]
        mask = bytes(int(s[i:i + 2]) % 256 for i in range(0, len(s), 2))
        t = bytearray(data)
        for i in range(len(t)): t[i] ^= mask[i % len(mask)]
        return bytes(t)
    def reverse_transform_19(self, data):
        if not data: return b''
        decimal.getcontext().prec = 60
        e = decimal.Decimal(1).exp(); five_e = decimal.Decimal(5) * e
        s = str(five_e).replace('.', '')[:max(10, len(data) // 2 + 5)]
        mask = bytes(int(s[i:i + 2]) % 256 for i in range(0, len(s), 2))
        t = bytearray(data)
        for i in range(len(t)): t[i] ^= mask[i % len(mask)]
        return bytes(t)

    def transform_20(self, data):
        if not data: return b''
        decimal.getcontext().prec = 60
        e = decimal.Decimal(1).exp(); five_e = decimal.Decimal(5) * e
        s = str(five_e).replace('.', '')[:max(10, len(data) // 2 + 5)]
        mask = bytes(int(s[i:i + 2]) % 256 for i in range(0, len(s), 2))
        t = bytearray(data)
        for i in range(len(t)): t[i] ^= mask[i % len(mask)]
        return bytes(t)
    reverse_transform_20 = transform_20

    def transform_21(self, data):
        if not data: return b''
        return bytes((b + 255) % 256 for b in data)
    def reverse_transform_21(self, data):
        if not data: return b''
        return bytes((b - 255) % 256 for b in data)

    # ---------------- 22-30 ----------------
    def transform_22(self, data): return base64.b64encode(data)
    def reverse_transform_22(self, data):
        try: return base64.b64decode(data, validate=False)
        except Exception as e: raise TransformError(f"b64: {e}")

    def transform_23(self, data):
        if not data: return b'\x00'
        try: text = data.decode('utf-8')
        except UnicodeDecodeError: return b'\x00' + data
        tokens = re.split(r'([A-Za-z0-9_]+)', text)
        wl = []; wi = {}; ts = []
        for i, tok in enumerate(tokens):
            if i % 2 == 1:
                wb = tok.encode('utf-8')
                idx = wi.get(wb)
                if idx is None:
                    idx = len(wl); wi[wb] = idx; wl.append(wb)
                ts.append((1, idx))
            else:
                ts.append((0, tok.encode('utf-8')))
        out = bytearray([1]) + struct.pack('>I', len(wl))
        for wb in wl: out += struct.pack('>I', len(wb)) + wb
        for typ, pay in ts:
            if typ == 1: out += b'\x01' + struct.pack('>I', pay)
            else: out += b'\x00' + struct.pack('>I', len(pay)) + pay
        tok_bytes = bytes(out)
        try:
            if self.reverse_transform_23(tok_bytes) == data: return tok_bytes
        except Exception: pass
        return b'\x00' + data

    def reverse_transform_23(self, data):
        if not data: return b''
        flag = data[0]
        if flag == 0: return data[1:]
        if flag != 1: raise TransformError(f"T23 flag {flag}")
        pos = 1
        if len(data) < pos + 4: raise TransformError("T23 short")
        nw = struct.unpack('>I', data[pos:pos + 4])[0]; pos += 4
        wl = []
        for _ in range(nw):
            if pos + 4 > len(data): raise TransformError("T23 t1")
            wlen = struct.unpack('>I', data[pos:pos + 4])[0]; pos += 4
            if pos + wlen > len(data): raise TransformError("T23 t2")
            wl.append(data[pos:pos + wlen]); pos += wlen
        out = bytearray()
        while pos < len(data):
            typ = data[pos]; pos += 1
            if typ == 1:
                if pos + 4 > len(data): raise TransformError("T23 i")
                idx = struct.unpack('>I', data[pos:pos + 4])[0]; pos += 4
                if idx >= len(wl): raise TransformError("T23 r")
                out += wl[idx]
            elif typ == 0:
                if pos + 4 > len(data): raise TransformError("T23 l")
                ll = struct.unpack('>I', data[pos:pos + 4])[0]; pos += 4
                if pos + ll > len(data): raise TransformError("T23 t3")
                out += data[pos:pos + ll]; pos += ll
            else: raise TransformError(f"T23 tok {typ}")
        return bytes(out)

    def transform_24(self, data): return self.transform_23(data)
    def reverse_transform_24(self, data): return self.reverse_transform_23(data)

    def _split_chunks(self, text):
        chunks = []
        for i, para in enumerate(re.split(r'(\n\n)', text)):
            if i % 2 == 1: chunks.append(para); continue
            for j, line in enumerate(re.split(r'(\n)', para)):
                if j % 2 == 1: chunks.append(line); continue
                for k, sent in enumerate(re.split(r'([.!?]+)', line)):
                    if k % 2 == 1: chunks.append(sent); continue
                    chunks.extend(re.split(r'(\s+|\b)', sent))
        return chunks

    def _dyn_tok(self, data, ib=3):
        try: text = data.decode('utf-8')
        except Exception: return b'\x00' + data
        chunks = self._split_chunks(text)
        freq = Counter(chunks)
        sc = sorted(freq.keys(), key=lambda x: (-freq[x], -len(x), x))
        ci = {ch: i for i, ch in enumerate(sc)}
        ne = len(sc)
        if ib == 2 and ne > 65535: ib = 3
        if ib == 3 and ne > 16777215: ib = 8
        h = bytearray([ib]) + struct.pack('>I', ne)
        for ch in sc:
            cb = ch.encode('utf-8')
            h += struct.pack('>I', len(cb)) + cb
        ts = bytearray()
        for ch in chunks:
            idx = ci[ch]
            if ib == 2: ts += struct.pack('>H', idx)
            elif ib == 3: ts += struct.pack('>I', idx)[1:4]
            else: ts += struct.pack('>Q', idx)
        return bytes(h) + bytes(ts)

    def _dyn_detok(self, data):
        if not data: return b''
        if data[0] == 0: return data[1:]
        ib = data[0]
        if ib not in (2, 3, 8): raise TransformError(f"dict ib {ib}")
        pos = 1
        if pos + 4 > len(data): raise TransformError("dict s")
        ne = struct.unpack('>I', data[pos:pos + 4])[0]; pos += 4
        dd = []
        for _ in range(ne):
            if pos + 4 > len(data): raise TransformError("dict t1")
            cl = struct.unpack('>I', data[pos:pos + 4])[0]; pos += 4
            if pos + cl > len(data): raise TransformError("dict t2")
            dd.append(data[pos:pos + cl].decode('utf-8')); pos += cl
        toks = []
        while pos < len(data):
            if ib == 2:
                if pos + 2 > len(data): break
                idx = struct.unpack('>H', data[pos:pos + 2])[0]; pos += 2
            elif ib == 3:
                if pos + 3 > len(data): break
                idx = struct.unpack('>I', b'\x00' + data[pos:pos + 3])[0]; pos += 3
            else:
                if pos + 8 > len(data): break
                idx = struct.unpack('>Q', data[pos:pos + 8])[0]; pos += 8
            if idx >= len(dd): raise TransformError(f"dict idx {idx}")
            toks.append(dd[idx])
        return ''.join(toks).encode('utf-8')

    def transform_25(self, data): return self._dyn_tok(data, 3)
    def reverse_transform_25(self, data): return self._dyn_detok(data)

    def transform_26(self, data):
        if not data: return b''
        secret = b"PJP_T26"
        r = bytearray()
        for idx in range(0, len(data), 1024):
            ch = data[idx:idx + 1024]; bn = idx // 1024
            h = hashlib.sha256(secret + struct.pack(">Q", bn)).digest()
            m = (h * ((len(ch) // len(h)) + 1))[:len(ch)]
            r.extend(a ^ b for a, b in zip(ch, m))
        return bytes(r)
    reverse_transform_26 = transform_26

    def transform_27(self, data):
        try: text = data.decode('utf-8')
        except UnicodeDecodeError: return b'\x00' + data
        for ch in text:
            if ch not in CHAR_TO_6BIT: return b'\x00' + data
        bits = []
        for ch in text:
            v = CHAR_TO_6BIT[ch]
            for i in range(5, -1, -1): bits.append((v >> i) & 1)
        pad = (8 - len(bits) % 8) % 8; bits.extend([0] * pad)
        out = bytearray()
        for i in range(0, len(bits), 8):
            b = 0
            for j in range(8): b = (b << 1) | bits[i + j]
            out.append(b)
        return b'\x01' + struct.pack('<I', len(text)) + bytes(out)

    def reverse_transform_27(self, data):
        if len(data) < 1: raise TransformError("T27")
        flag = data[0]
        if flag == 0: return data[1:]
        if flag != 1: raise TransformError(f"T27 {flag}")
        p = data[1:]
        if len(p) < 4: raise TransformError("T27 p")
        nc = struct.unpack('<I', p[:4])[0]; packed = p[4:]
        nb = (nc * 6 + 7) // 8
        if len(packed) != nb: raise TransformError("T27 mm")
        pb = (8 - (nc * 6) % 8) % 8
        if pb > 0 and packed:
            m = (1 << pb) - 1
            if packed[-1] & m: raise TransformError("T27 pad")
        bits = []
        for b in packed:
            for i in range(7, -1, -1): bits.append((b >> i) & 1)
        chars = []
        for i in range(nc):
            v = 0
            for j in range(6): v = (v << 1) | bits[i * 6 + j]
            if v >= 64: raise TransformError(f"T27 v {v}")
            chars.append(SIXBIT_TO_CHAR[v])
        return ''.join(chars).encode('utf-8')

    def transform_28(self, data):
        if not data: return b'\x00'
        pad = (3 - len(data) % 3) % 3
        padded = data + b'\x00' * pad
        out = bytearray([pad])
        for i in range(0, len(padded), 3):
            v = int.from_bytes(padded[i:i + 3], 'little')
            bi = i // 3; k = (bi * 65537 + 12345) & 0xFFFF
            out.extend(((v - k) % (1 << 24)).to_bytes(3, 'little'))
        return bytes(out)
    def reverse_transform_28(self, data):
        if data == b'\x00': return b''
        if not data: raise TransformError("T28")
        pad = data[0]; p = data[1:]
        if len(p) % 3 != 0: raise TransformError("T28 l")
        out = bytearray()
        for i in range(0, len(p), 3):
            v = int.from_bytes(p[i:i + 3], 'little')
            bi = i // 3; k = (bi * 65537 + 12345) & 0xFFFF
            out.extend(((v + k) % (1 << 24)).to_bytes(3, 'little'))
        if pad: out = out[:-pad]
        return bytes(out)

    def _best16(self, data):
        if len(data) < 3: return 0
        pad = (3 - len(data) % 3) % 3
        padded = data + b'\x00' * pad
        vals = [int.from_bytes(padded[i:i + 3], 'little') for i in range(0, len(padded), 3)]
        bk, bc = 0, float('inf')
        for k in range(65536):
            tr = [(v - k) & 0xFFFFFF for v in vals]
            m = sum(tr) // len(tr)
            c = sum(abs(t - m) for t in tr)
            if c < bc: bc = c; bk = k
            if c == 0: break
        return bk

    def transform_29(self, data):
        if not data: return b'\x00'
        k = self._best16(data)
        pad = (3 - len(data) % 3) % 3
        padded = data + b'\x00' * pad
        out = bytearray([pad]) + k.to_bytes(2, 'little')
        for i in range(0, len(padded), 3):
            v = int.from_bytes(padded[i:i + 3], 'little')
            out.extend(((v - k) % (1 << 24)).to_bytes(3, 'little'))
        return bytes(out)
    def reverse_transform_29(self, data):
        if data == b'\x00': return b''
        if len(data) < 3: raise TransformError("T29")
        pad = data[0]; k = int.from_bytes(data[1:3], 'little')
        p = data[3:]
        if len(p) % 3 != 0: raise TransformError("T29 l")
        out = bytearray()
        for i in range(0, len(p), 3):
            v = int.from_bytes(p[i:i + 3], 'little')
            out.extend(((v + k) % (1 << 24)).to_bytes(3, 'little'))
        if pad: out = out[:-pad]
        return bytes(out)

    def transform_30(self, data):
        if not data: return b'\x00'
        pad = (3 - len(data) % 3) % 3
        padded = data + b'\x00' * pad
        vals = [int.from_bytes(padded[i:i + 3], 'little') for i in range(0, len(padded), 3)]
        mean = sum(vals) // len(vals)
        sv = sorted(vals); med = sv[len(sv) // 2]
        cands = set()
        for b in [mean, med]:
            for o in [0, 1, -1, 10, -10, 100, -100, 1000, -1000]:
                cands.add((b + o) % (1 << 24))
        rng = random.Random(42)
        for _ in range(10): cands.add(rng.randint(0, (1 << 24) - 1))
        bk, bc = 0, float('inf')
        for k in cands:
            tr = [(v - k) & 0xFFFFFF for v in vals]
            m = sum(tr) // len(tr)
            c = sum(abs(t - m) for t in tr)
            if c < bc: bc = c; bk = k
        out = bytearray([pad]) + bk.to_bytes(3, 'little')
        for i in range(0, len(padded), 3):
            v = int.from_bytes(padded[i:i + 3], 'little')
            out.extend(((v - bk) % (1 << 24)).to_bytes(3, 'little'))
        return bytes(out)
    def reverse_transform_30(self, data):
        if data == b'\x00': return b''
        if len(data) < 4: raise TransformError("T30")
        pad = data[0]; k = int.from_bytes(data[1:4], 'little')
        p = data[4:]
        if len(p) % 3 != 0: raise TransformError("T30 l")
        out = bytearray()
        for i in range(0, len(p), 3):
            v = int.from_bytes(p[i:i + 3], 'little')
            out.extend(((v + k) % (1 << 24)).to_bytes(3, 'little'))
        if pad: out = out[:-pad]
        return bytes(out)

    def transform_31(self, d): return d
    reverse_transform_31 = transform_31
    def transform_32(self, d): return d
    reverse_transform_32 = transform_32

    # ---------------- PAQJP 33-40 ----------------
    def _paqjp_t23(self, data):
        if not data: return b'\x00' * 5
        bits = []
        for b in data:
            for i in range(7, -1, -1): bits.append((b >> i) & 1)
        return self._compress_bits(bits)

    def _paqjp_r23(self, data):
        if not data or data == b'\x00' * 5: return b''
        bits = self._decompress_bits(data)
        if not bits: return b''
        out = bytearray()
        for i in range(0, len(bits), 8):
            v = 0
            for j in range(i, min(i + 8, len(bits))): v = (v << 1) | bits[j]
            if i + 8 > len(bits): v <<= (8 - (len(bits) - i))
            out.append(v)
        return bytes(out)
    def _compress_bits(self, bits):
        obl = len(bits)
        if obl == 0: return b'\x00' * 5
        cur = bits[:]; pl = obl; pc = 0
        while pc < 255:
            pad = (4 - len(cur) % 4) % 4
            padded = cur + [0] * pad
            nc = len(padded) // 4; enc = []
            for i in range(nc):
                nib = (padded[i * 4] << 3) | (padded[i * 4 + 1] << 2) | (padded[i * 4 + 2] << 1) | padded[i * 4 + 3]
                L, cw = _CONST_DIAPASON_ITER_CODE[nib]
                for b in range(L - 1, -1, -1): enc.append((cw >> b) & 1)
            if len(enc) < pl: cur = enc; pl = len(enc); pc += 1
            else: break
        cbl = len(cur)
        hdr = struct.pack('>H', obl) + bytes([pc]) + struct.pack('>H', cbl)
        pad = (8 - len(cur) % 8) % 8; cur += [0] * pad
        out = bytearray()
        for i in range(0, len(cur), 8):
            v = 0
            for j in range(8): v = (v << 1) | cur[i + j]
            out.append(v)
        return hdr + bytes(out)
    def _decompress_bits(self, data):
        if len(data) < 5: raise TransformError("Diap")
        obl = struct.unpack('>H', data[:2])[0]
        pc = data[2]
        cbl = struct.unpack('>H', data[3:5])[0]
        pay = data[5:]
        bits = []
        for b in pay:
            for i in range(7, -1, -1): bits.append((b >> i) & 1)
        if len(bits) < cbl: raise TransformError("Diap p")
        cur = bits[:cbl]
        if pc == 0: return cur[:obl]
        for _ in range(pc):
            pos = 0; nb = len(cur); dn = []
            while pos < nb:
                m = False
                for L in range(2, 10):
                    if pos + L > nb: continue
                    cw = 0
                    for k in range(L): cw = (cw << 1) | cur[pos + k]
                    if (L, cw) in _CONST_DIAPASON_ITER_DECODE:
                        dn.append(_CONST_DIAPASON_ITER_DECODE[(L, cw)])
                        pos += L; m = True; break
                if not m: raise TransformError("Diap cw")
            new_bits = []
            for nib in dn:
                for j in range(3, -1, -1): new_bits.append((nib >> j) & 1)
            cur = new_bits
        if len(cur) < obl: raise TransformError("Diap s")
        return cur[:obl]

    def _paqjp_t24(self, data):
        if not data: return struct.pack('>I', 0)
        MAX = 43; bits = []; i = 0; n = len(data)
        while i < n:
            cl = min(MAX, n - i); ch = data[i:i + cl]
            f = ch[0]; same = all(b == f for b in ch)
            if same:
                self._append_bits(bits, 1, 1); self._append_bits(bits, f, 8)
                self._append_bits(bits, cl - 1, 6)
            else:
                self._append_bits(bits, 0, 1); self._append_bits(bits, cl, 6)
                for b in ch: self._append_bits(bits, b, 8)
            i += cl
        pad = (8 - len(bits) % 8) % 8; self._append_bits(bits, 0, pad)
        out = bytearray()
        for j in range(0, len(bits), 8):
            b = 0
            for k in range(8): b = (b << 1) | bits[j + k]
            out.append(b)
        return struct.pack('>I', len(data)) + bytes(out)
    def _paqjp_r24(self, data):
        if not data: return b''
        if len(data) < 4: raise TransformError("BlkRun")
        ol = struct.unpack('>I', data[:4])[0]
        p = data[4:]
        bits = []
        for b in p:
            for i in range(7, -1, -1): bits.append((b >> i) & 1)
        pos = 0; nb = len(bits); out = bytearray()
        while pos < nb and len(out) < ol:
            if pos + 1 > nb: break
            flag = self._read_bits(bits, pos, 1); pos += 1
            if flag == 1:
                if pos + 14 > nb: raise TransformError("BlkRun t")
                bv = self._read_bits(bits, pos, 8); pos += 8
                cm = self._read_bits(bits, pos, 6); pos += 6
                rl = min(cm + 1, ol - len(out))
                out.extend([bv] * rl)
            else:
                if pos + 6 > nb: raise TransformError("BlkRun l")
                cl = self._read_bits(bits, pos, 6); pos += 6
                if cl == 0: break
                if pos + cl * 8 > nb: raise TransformError("BlkRun b")
                for _ in range(cl):
                    out.append(self._read_bits(bits, pos, 8)); pos += 8
        return bytes(out[:ol])

    def _paqjp_t25(self, data):
        if not data: return b'\x01'
        n = 3; res = bytearray(data)
        for i in range(len(res)): res[i] = (pow(res[i] + 1, n, 257) - 1) & 0xFF
        return bytes([n]) + bytes(res)
    def _paqjp_r25(self, data):
        if data == b'\x01': return b''
        if len(data) < 2: raise TransformError("FLT25")
        n = data[0]; inv = mod_inv(n, 256)
        if inv is None: raise TransformError(f"FLT25 {n}")
        res = bytearray(data[1:])
        for i in range(len(res)): res[i] = (pow(res[i] + 1, inv, 257) - 1) & 0xFF
        return bytes(res)

    def _paqjp_t26(self, data):
        if not data: return b'\x01\x00'
        n = (len(data) * 7 + 13) & 0xFFFF
        if n % 2 == 0: n ^= 1
        e = pow(n, 16777216, 256) | 1
        res = bytearray(data)
        for i in range(len(res)): res[i] = (pow(res[i] + 1, e, 257) - 1) & 0xFF
        return bytes([n & 0xFF, (n >> 8) & 0xFF]) + bytes(res)
    def _paqjp_r26(self, data):
        if data == b'\x01\x00': return b''
        if len(data) < 2: raise TransformError("FLT26")
        n = data[0] | (data[1] << 8)
        if n % 2 == 0: n ^= 1
        e = pow(n, 16777216, 256) | 1
        inv = mod_inv(e, 256)
        if inv is None: raise TransformError(f"FLT26 {e}")
        res = bytearray(data[2:])
        for i in range(len(res)): res[i] = (pow(res[i] + 1, inv, 257) - 1) & 0xFF
        return bytes(res)

    def _paqjp_t27(self, data):
        if not data:
            o = bytearray(b'\x00\x00\x00\x00\x01\x00'); o.extend(b'\x00' * 1024)
            return bytes(o)
        BS = 1024; tb = (len(data) + BS - 1) // BS
        out = bytearray(); out.extend(len(data).to_bytes(4, 'big'))
        for bi in range(tb):
            s = bi * BS; e = min(s + BS, len(data))
            ch = data[s:e]; pad = BS - len(ch)
            if pad: ch = ch + b'\x00' * pad
            n = ((len(data) * 7 + bi * 13 + 1) & 0xFFFF) | 1
            e_ = pow(n, 16777216, 256) | 1
            e200 = pow(e_, 200, 256)
            t = bytearray(ch)
            for i in range(BS): t[i] = (pow(t[i] + 1, e200, 257) - 1) & 0xFF
            out.append(n & 0xFF); out.append((n >> 8) & 0xFF); out.extend(t)
        return bytes(out)
    def _paqjp_r27(self, data):
        if len(data) < 4: raise TransformError("FLT27")
        ol = int.from_bytes(data[:4], 'big')
        p = data[4:]; BS = 1024; btl = 2 + BS
        if len(p) % btl != 0: raise TransformError("FLT27 a")
        nb = len(p) // btl; dec = bytearray()
        for bi in range(nb):
            off = bi * btl
            n = p[off] | (p[off + 1] << 8); ch = p[off + 2:off + 2 + BS]
            n |= 1
            e_ = pow(n, 16777216, 256) | 1
            e200 = pow(e_, 200, 256)
            inv = mod_inv(e200, 256)
            if inv is None: raise TransformError(f"FLT27 {e200}")
            for i in range(BS): dec.append((pow(ch[i] + 1, inv, 257) - 1) & 0xFF)
        return bytes(dec[:ol])

    def _compress_backend_with_flag(self, data):
        cands = []
        try: cands.append((1, zstd_cctx.compress(data)))
        except Exception: pass
        if paq is not None:
            try: cands.append((2, paq.compress(data)))
            except Exception: pass
        if HAS_BROTLI:
            try: cands.append((3, brotli.compress(data, quality=11)))
            except Exception: pass
        cands.append((0, data))
        bf, bd = min(cands, key=lambda x: len(x[1]))
        return bytes([bf]) + bd
    def _decompress_backend_with_flag(self, data):
        if not data: return b''
        f = data[0]; p = data[1:]
        if f == 0: return p
        if f == 1: return zstd_dctx.decompress(p)
        if f == 2 and paq is not None: return paq.decompress(p)
        if f == 3 and HAS_BROTLI: return brotli.decompress(p)
        raise TransformError(f"bkf {f}")

    def _paqjp_t28(self, data):
        BS = 1024
        if not data:
            ch = b'\x00' * BS; c = self._compress_backend_with_flag(ch)
            o = bytearray(struct.pack('>I', 0))
            o += b'\x01\x00' + bytes([(len(c) >> 8) & 0xFF, len(c) & 0xFF]) + c
            return bytes(o)
        tb = (len(data) + BS - 1) // BS
        out = bytearray(); out.extend(len(data).to_bytes(4, 'big'))
        for bi in range(tb):
            s = bi * BS; e = min(s + BS, len(data))
            ch = data[s:e] + b'\x00' * (BS - len(data[s:e]))
            n = ((len(data) * 7 + bi * 13 + 1) & 0xFFFF) | 1
            e_ = pow(n, 16777216, 256) | 1; e200 = pow(e_, 200, 256)
            t = bytearray(ch)
            for i in range(BS): t[i] = (pow(t[i] + 1, e200, 257) - 1) & 0xFF
            c = self._compress_backend_with_flag(bytes(t))
            out += bytes([n & 0xFF, (n >> 8) & 0xFF,
                          (len(c) >> 8) & 0xFF, len(c) & 0xFF]) + c
        return bytes(out)
    def _paqjp_r28(self, data):
        if len(data) < 4: raise TransformError("FLT28")
        ol = int.from_bytes(data[:4], 'big'); p = data[4:]
        pos = 0; dec = bytearray()
        while pos < len(p):
            n = p[pos] | (p[pos + 1] << 8); pos += 2
            cl = (p[pos] << 8) | p[pos + 1]; pos += 2
            cb = p[pos:pos + cl]; pos += cl
            b = self._decompress_backend_with_flag(cb)
            n |= 1; e_ = pow(n b, 16777216, 256) | 1; e'\x00'200 = pow(e_, 200, 256)
            inv = mod_inv(e200, 256)
            if inv is None: raise TransformError(f"FLT28 {e200}")
            t = bytearray(b)
            for i in range(len(t)): t[i] = (pow(t[i] + 1, inv, 257) - 1) & 0xFF
            dec.extend(t)
        return bytes(dec[:ol])

    def _paqjp_t29(self, data):
        BS = 32
        if not data:
            ch = * BS; c = self._compress_backend_with_flag(ch)
            o = bytearray(struct.pack('>I', 0))
            o += b'\x01\x00' + bytes([(len(c) >> 8) & 0xFF, len(c) & 0xFF]) + c
            return bytes(o)
        tb = (len(data) + BS - 1) // BS
        out = bytearray(); out.extend(len(data).to_bytes(4, 'big'))
        for bi in range(tb):
            s = bi * BS; e = min(s + BS, len(data))
            ch = data[s:e] + b'\x00' * (BS - len(data[s:e]))
            n = ((len(data) * 7 + bi * 13 + 1) & 0xFFFF) | 1
            c = self._compress_backend_with_flag(bytes(ch))
            out += bytes([n & 0xFF, (n >> 8) & 0xFF,
                          (len(c) >> 8) & 0xFF, len(c) & 0xFF]) + c
        return bytes(out)
    def _paqjp_r29(self, data):
        if len(data) < 4: raise TransformError("FLT29")
        ol = int.from_bytes(data[:4], 'big'); p = data[4:]
        pos = 0; dec = bytearray()
        while pos < len(p):
            n = p[pos] | (p[pos + 1] << 8); pos += 2
            cl = (p[pos] << 8) | p[pos + 1]; pos += 2
            cb = p[pos:pos + cl]; pos += cl
            dec.extend(self._decompress_backend_with_flag(cb))
        return bytes(dec[:ol])

    def _paqjp_t30(self, data):
        BS = 33
        if not data:
            ch = b'\x00' * BS; c = self._compress_backend_with_flag(ch)
            o = bytearray(struct.pack('>I', 0))
            o += b'\x01\x01' + bytes([(len(c) >> 8) & 0xFF, len(c) & 0xFF]) + c
            return bytes(o)
        tb = (len(data) + BS - 1) // BS
        out = bytearray(); out.extend(len(data).to_bytes(4, 'big'))
        for bi in range(tb):
            s = bi * BS; e = min(s + BS, len(data))
            ch = data[s:e] + b'\x00' * (BS - len(data[s:e]))
            h = hashlib.sha256(ch + bytes([bi & 0xFF, (len(data) >> 8) & 0xFF,
                                           len(data) & 0xFF])).digest()
            enc = bytes([32]) + h
            c = self._compress_backend_with_flag(ch)
            out += enc + bytes([(len(c) >> 8) & 0xFF, len(c) & 0xFF]) + c
        return bytes(out)
    def _paqjp_r30(self, data):
        if len(data) < 4: raise TransformError("FLT30")
        ol = int.from_bytes(data[:4], 'big'); p = data[4:]
        pos = 0; dec = bytearray()
        while pos < len(p):
            Ln = p[pos]; pos += 1
            if Ln > 32 or pos + Ln > len(p): raise TransformError("FLT30 n")
            pos += Ln
            cl = (p[pos] << 8) | p[pos + 1]; pos += 2
            cb = p[pos:pos + cl]; pos += cl
            dec.extend(self._decompress_backend_with_flag(cb))
        return bytes(dec[:ol])

    # ---------------- 41-47 ----------------
    def transform_41(self, data):
        if not data: return b''
        t = bytearray(data); m = bytes([0x27, 0x03])
        for i in range(min(len(t), 8)): t[i] ^= m[i % 2]
        return bytes(t)
    reverse_transform_41 = transform_41
    def transform_42(self, data):
        if not data: return b''
        t = bytearray(data); m = bytes([0x27, 0x03])
        for i in range(len(t)): t[i] ^= m[i % 2]
        return bytes(t)
    reverse_transform_42 = transform_42
    def transform_43(self, data):
        if not data: return b''
        t = bytearray(data); m = bytes([0x10, 0x00, 0x00])
        for i in range(0, len(t), 3):
            for j in range(min(3, len(t) - i)): t[i + j] ^= m[j]
        return bytes(t)
    reverse_transform_43 = transform_43
    def transform_44(self, data):
        if not data: return b''
        return base64.b64encode(data)
    def reverse_transform_44(self, data):
        if not data: return b''
        try: return base64.b64decode(data, validate=False)
        except Exception as e: raise TransformError(f"b64-44 {e}")

    @staticmethod
    def _huffman_code_lengths(freq):
        heap = [(f, i, i) for i, f in enumerate(freq) if f > 0]
        if not heap: return [0] * len(freq)
        if len(heap) == 1:
            L = [0] * len(freq); L[heap[0][2]] = 1; return L
        heapq.heapify(heap); nid = len(freq)
        while len(heap) > 1:
            f1, _, n1 = heapq.heappop(heap); f2, _, n2 = heapq.heappop(heap)
            heapq.heappush(heap, (f1 + f2, nid, (n1, n2))); nid += 1
        L = [0] * len(freq)
        def trav(n, d):
            if isinstance(n, int): L[n] = d
            else: trav(n[0], d + 1); trav(n[1], d + 1)
        trav(heap[0][2], 0); return L
    @staticmethod
    def _huffman_canonical_codes(L):
        syms = sorted(range(len(L)), key=lambda s: (L[s], s))
        codes = {}; c = 0; pl = 0; first = True
        for s in syms:
            cl = L[s]
            if cl == 0: continue
            if first: pl = cl; first = False
            elif cl != pl: c <<= (cl - pl); pl = cl
            codes[s] = (c, cl); c += 1
        return codes

    def transform_45(self, data):
        if not data: return b''
        freq = [0] * 256
        for b in data: freq[b] += 1
        cl = self._huffman_code_lengths(freq); codes = self._huffman_canonical_codes(cl)
        hdr = bytearray(len(data).to_bytes(4, 'big')); hdr.extend(cl)
        bits = []
        for b in data:
            c, n = codes[b]
            for i in range(n - 1, -1, -1): bits.append((c >> i) & 1)
        pad = (8 - len(bits) % 8) % 8; bits.extend([0] * pad)
        out = bytearray()
        for i in range(0, len(bits), 8):
            v = 0
            for j in range(8): v = (v << 1) | bits[i + j]
            out.append(v)
        return bytes(hdr) + bytes(out)
    def reverse_transform_45(self, data):
        if not data: return b''
        if len(data) < 4 + 256: raise TransformError("Huff")
        ol = int.from_bytes(data[:4], 'big'); cl = list(data[4:260]); p = data[260:]
        if ol == 0: return b''
        if max(cl) > 32: raise TransformError("Huff l")
        code_to = {}
        syms = sorted(range(256), key=lambda s: (cl[s], s))
        c = 0; pl = 0; first = True
        for s in syms:
            L = cl[s]
            if L == 0: continue
            if first: pl = L; first = False
            elif L != pl: c <<= (L - pl); pl = L
            code_to[(L, c)] = s; c += 1
        bits = []
        for b in p:
            for i in range(7, -1, -1): bits.append((b >> i) & 1)
        pos = 0; nb = len(bits); out = bytearray()
        mx = max(cl) if any(cl) else 0
        while pos < nb and len(out) < ol:
            f = False
            for L in range(1, mx + 1):
                if pos + L > nb: break
                v = 0
                for j in range(L): v = (v << 1) | bits[pos + j]
                if (L, v) in code_to:
                    out.append(code_to[(L, v)]); pos += L; f = True; break
            if not f: raise TransformError(f"Huff p {pos}")
        if len(out) != ol: raise TransformError(f"Huff {len(out)}!={ol}")
        return bytes(out)

    def transform_46(self, data):
        if not data: return b''
        t = bytearray(data); m = self.mask_46
        for i in range(len(t)): t[i] ^= m[i % len(m)]
        return bytes(t)
    reverse_transform_46 = transform_46
    def transform_47(self, data):
        if not data: return b''
        t = bytearray(data); tl = len(self.mod_state_table)
        if tl == 0: return data
        for i in range(len(t)): t[i] ^= self.mod_state_table[i % tl][0]
        return bytes(t)
    reverse_transform_47 = transform_47

    def transform_57(self, data):
        if len(data) < 4:
            pad = 4 - len(data); k = 0
            return bytes([pad]) + k.to_bytes(4, 'little') + data + b'\x00' * pad
        n = len(data); pad = (4 - n % 4) % 4
        padded = data + b'\x00' * pad
        blocks = [padded[i:i + 4] for i in range(0, len(padded), 4)]
        mc, _ = Counter(blocks).most_common(1)[0]
        k = int.from_bytes(mc, 'little')
        out = bytearray()
        for blk in blocks:
            out.extend((int.from_bytes(blk, 'little') ^ k).to_bytes(4, 'little'))
        return bytes([pad]) + k.to_bytes(4, 'little') + bytes(out)
    def reverse_transform_57(self, data):
        if len(data) < 5: raise TransformError("T57")
        pad = data[0]; k = int.from_bytes(data[1:5], 'little')
        p = data[5:]
        if len(p) % 4 != 0: raise TransformError("T57 l")
        out = bytearray()
        for i in range(0, len(p), 4):
            out.extend((int.from_bytes(p[i:i + 4], 'little') ^ k).to_bytes(4, 'little'))
        if pad: out = out[:-pad]
        return bytes(out)

    def _dynamic(self, n):
        def tf(data):
            if not data: return b''
            sd = self.get_seed(n % len(self.seed_tables), len(data))
            return bytes(b ^ sd for b in data)
        return tf, tf

    def transform_256(self, d): return d
    reverse_transform_256 = transform_256

    def _build_transform_maps(self):
        self.fwd_transforms = {}
        self.rev_transforms = {}
        for i in range(1, 22):
            self.fwd_transforms[i] = getattr(self, f"transform_{i:02d}")
            self.rev_transforms[i] = getattr(self, f"reverse_transform_{i:02d}")
        self.fwd_transforms[22] = self.transform_22; self.rev_transforms[22] = self.reverse_transform_22
        self.fwd_transforms[23] = self.transform_23; self.rev_transforms[23] = self.reverse_transform_23
        self.fwd_transforms[24] = self.transform_24; self.rev_transforms[24] = self.reverse_transform_24
        self.fwd_transforms[25] = self.transform_25; self.rev_transforms[25] = self.reverse_transform_25
        self.fwd_transforms[26] = self.transform_26; self.rev_transforms[26] = self.reverse_transform_26
        self.fwd_transforms[27] = self.transform_27; self.rev_transforms[27] = self.reverse_transform_27
        self.fwd_transforms[28] = self.transform_28; self.rev_transforms[28] = self.reverse_transform_28
        self.fwd_transforms[29] = self.transform_29; self.rev_transforms[29] = self.reverse_transform_29
        self.fwd_transforms[30] = self.transform_30; self.rev_transforms[30] = self.reverse_transform_30
        self.fwd_transforms[31] = self.transform_31; self.rev_transforms[31] = self.reverse_transform_31
        self.fwd_transforms[32] = self.transform_32; self.rev_transforms[32] = self.reverse_transform_32
        self.fwd_transforms[33] = self._paqjp_t23; self.rev_transforms[33] = self._paqjp_r23
        self.fwd_transforms[34] = self._paqjp_t24; self.rev_transforms[34] = self._paqjp_r24
        self.fwd_transforms[35] = self._paqjp_t25; self.rev_transforms[35] = self._paqjp_r25
        self.fwd_transforms[36] = self._paqjp_t26; self.rev_transforms[36] = self._paqjp_r26
        self.fwd_transforms[37] = self._paqjp_t27; self.rev_transforms[37] = self._paqjp_r27
        self.fwd_transforms[38] = self._paqjp_t28; self.rev_transforms[38] = self._paqjp_r28
        self.fwd_transforms[39] = self._paqjp_t29; self.rev_transforms[39] = self._paqjp_r29
        self.fwd_transforms[40] = self._paqjp_t30; self.rev_transforms[40] = self._paqjp_r30
        self.fwd_transforms[41] = self.transform_41; self.rev_transforms[41] = self.reverse_transform_41
        self.fwd_transforms[42] = self.transform_42; self.rev_transforms[42] = self.reverse_transform_42
        self.fwd_transforms[43] = self.transform_43; self.rev_transforms[43] = self.reverse_transform_43
        self.fwd_transforms[44] = self.transform_44; self.rev_transforms[44] = self.reverse_transform_44
        self.fwd_transforms[45] = self.transform_45; self.rev_transforms[45] = self.reverse_transform_45
        self.fwd_transforms[46] = self.transform_46; self.rev_transforms[46] = self.reverse_transform_46
        self.fwd_transforms[47] = self.transform_47; self.rev_transforms[47] = self.reverse_transform_47
        for i in range(48, 57):
            f, r = self._dynamic(i); self.fwd_transforms[i] = f; self.rev_transforms[i] = r
        self.fwd_transforms[57] = self.transform_57; self.rev_transforms[57] = self.reverse_transform_57
        for i in range(58, 256):
            f, r = self._dynamic(i); self.fwd_transforms[i] = f; self.rev_transforms[i] = r
        self.fwd_transforms[256] = self.transform_256; self.rev_transforms[256] = self.reverse_transform_256

    def _precompute_quantum_transforms(self):
        if not USE_QUANTUM or not HAS_QISKIT: return
        q = self.QUANTUM_QUBITS
        if q > 49: q = 49
        size = 1 << q
        bs = size if q <= 12 else 1024
        for i in range(8):
            rng = random.Random(1000 + i)
            perm = list(range(size)); rng.shuffle(perm)
            if len(perm) > bs: perm = perm[:bs]
            inv = [0] * len(perm)
            for j, p in enumerate(perm): inv[p] = j
            def fwd(data, p=perm): return bytes(p[b] if b < len(p) else b for b in data)
            def rev(data, iv=inv): return bytes(iv[b] if b < len(iv) else b for b in data)
            self.fwd_transforms[256 + i + 1] = fwd
            self.rev_transforms[256 + i + 1] = rev

    # ---------------- Header ----------------
    def _encode_marker_single(self, t):
        if t <= 252: return bytes([t - 1])
        elif t <= 255: return bytes([254, t - 253])
        return bytes([255, (t - 256) // 256, (t - 256) % 256])
    def _encode_marker_raw(self): return bytes([252])
    def _decode_header(self, data):
        if len(data) < 1: return 0, ()
        f = data[0]
        if f < 252: return 1, (f + 1,)
        if f == 252: return 1, ()
        if f == 254:
            if len(data) < 2: return 0, ()
            x = data[1]
            return (2, (253 + x,)) if x <= 3 else (0, ())
        if f == 255:
            if len(data) < 3: return 0, ()
            return 3, (256 + data[1] * 256 + data[2],)
        return 0, ()

    # ---------------- Backends ----------------
    def _compress_backend(self, data):
        cands = [(0, data)]
        try:
            c = zstd_cctx.compress(data)
            if len(c) >= 4 and c[:4] == b'\x28\xb5\x2f\xfd': c = c[4:]
            cands.append((1, c))
        except Exception: pass
        if paq is not None:
            try:
                pd = paq.compress(data)
                if len(pd) >= 7 and pd[:4] == b'\x00\x63\x00\x00' and pd[-3:] == b'\xff\xff\xff':
                    cands.append((3, pd[4:-3]))
                else:
                    cands.append((2, pd))
            except Exception: pass
        if HAS_BROTLI:
            try: cands.append((4, brotli.compress(data, quality=11)))
            except Exception: pass
        bf, bd = min(cands, key=lambda x: len(x[1]))
        return bytes([bf]) + bd
    def _decompress_backend(self, data):
        if len(data) < 1: return None
        f = data[0]; p = data[1:]
        if f == 0: return p
        if f == 1:
            try: return zstd_dctx.decompress(b'\x28\xb5\x2f\xfd' + p)
            except Exception: return None
        if f == 2 and paq is not None:
            try: return paq.decompress(p)
            except Exception: return None
        if f == 3 and paq is not None:
            try: return paq.decompress(b'\x00\x63\x00\x00' + p + b'\xff\xff\xff')
            except Exception: return None
        if f == 4 and HAS_BROTLI:
            try: return brotli.decompress(p)
            except Exception: return None
        return None

    # ---------------- LZH ----------------
    def _lz77_tokenize(self, data):
        tokens = []; i = 0; n = len(data)
        while i < n:
            bl = 0; bd = 0
            sw = max(0, i - self.WINDOW_SIZE)
            for j in range(sw, i):
                if data[j] != data[i]: continue
                k = 0
                while i + k < n and j + k < i and data[j + k] == data[i + k]:
                    k += 1
                    if k >= self.MAX_MATCH: break
                if k >= self.MIN_MATCH and k > bl:
                    bl = k; bd = i - j
                    if bl == self.MAX_MATCH: break
            if bl >= self.MIN_MATCH:
                tokens.append(('M', bd, bl)); i += bl
            else:
                tokens.append(('L', data[i], None)); i += 1
        return tokens
    def _lz77_untokenize(self, tokens):
        out = bytearray()
        for t in tokens:
            if t[0] == 'L': out.append(t[1])
            else:
                d, l = t[1], t[2]
                st = len(out) - d
                for k in range(l): out.append(out[st + k])
        return bytes(out)
    def _encode_lzh(self, data):
        tokens = self._lz77_tokenize(data)
        lf = [0] * 256; df = [0] * (self.MAX_DIST + 1); nf = [0] * (self.MAX_MATCH + 1)
        for t in tokens:
            if t[0] == 'L': lf[t[1]] += 1
            else: df[t[1]] += 1; nf[t[2]] += 1
        lcl = self._huffman_code_lengths(lf)
        dcl = self._huffman_code_lengths(df)
        ncl = self._huffman_code_lengths(nf)
        lcs = self._huffman_canonical_codes(lcl)
        dcs = self._huffman_canonical_codes(dcl)
        ncs = self._huffman_canonical_codes(ncl)
        bits = []
        tc = len(tokens)
        for b in struct.pack('>I', tc):
            for i in range(8): bits.append((b >> (7 - i)) & 1)
        for t in tokens:
            if t[0] == 'L':
                bits.append(0)
                c, n = lcs[t[1]]
                for i in range(n - 1, -1, -1): bits.append((c >> i) & 1)
            else:
                bits.append(1)
                cd, nd = dcs[t[1]]
                for i in range(nd - 1, -1, -1): bits.append((cd >> i) & 1)
                cl, nl = ncs[t[2]]
                for i in range(nl - 1, -1, -1): bits.append((cl >> i) & 1)
        pad = (8 - len(bits) % 8) % 8; bits.extend([0] * pad)
        def pk(L): return b''.join(struct.pack('>H', x) for x in L)
        header = bytearray()
        header.extend(pk(lcl)); header.extend(pk(dcl)); header.extend(pk(ncl))
        out = bytearray(header)
        for i in range(0, len(bits), 8):
            b = 0
            for j in range(8): b = (b << 1) | bits[i + j]
            out.append(b)
        return bytes(out)
    def _decode_lzh(self, data):
        LL = 256 * 2; DL = 2049 * 2; NL = 2049 * 2
        if len(data) < LL + DL + NL: raise TransformError("LZH short")
        pos = 0
        lcl = [struct.unpack('>H', data[i:i + 2])[0] for i in range(pos, pos + LL, 2)]; pos += LL
        dcl = [struct.unpack('>H', data[i:i + 2])[0] for i in range(pos, pos + DL, 2)]; pos += DL
        ncl = [struct.unpack('>H', data[i:i + 2])[0] for i in range(pos, pos + NL, 2)]; pos += NL
        def bdt(L):
            syms = sorted(range(len(L)), key=lambda s: (L[s], s))
            d = {}; c = 0; pl = 0; first = True
            for s in syms:
                cl = L[s]
                if cl == 0: continue
                if first: pl = cl; first = False
                elif cl != pl: c <<= (cl - pl); pl = cl
                d[(cl, c)] = s; c += 1
            return d
        ld = bdt(lcl); dd = bdt(dcl); nd = bdt(ncl)
        mlb = max(lcl) if any(lcl) else 0
        mdb = max(dcl) if any(dcl) else 0
        mnb = max(ncl) if any(ncl) else 0
        p = data[pos:]
        if len(p) < 4: raise TransformError("LZH empty")
        tc = struct.unpack('>I', p[:4])[0]
        bits = []
        for byte in p[4:]:
            for i in range(7, -1, -1): bits.append((byte >> i) & 1)
        bpos = 0; tokens = []
        for _ in range(tc):
            if bpos >= len(bits): raise TransformError("LZH eof")
            flag = bits[bpos]; bpos += 1
            if flag == 0:
                found = False
                for cl in range(1, mlb + 1):
                    if bpos + cl > len(bits): break
                    v = 0
                    for j in range(cl): v = (v << 1) | bits[bpos + j]
                    if (cl, v) in ld:
                        tokens.append(('L', ld[(cl, v)], None)); bpos += cl
                        found = True; break
                if not found: raise TransformError("LZH lit")
            else:
                fd = False
                for cl in range(1, mdb + 1):
                    if bpos + cl > len(bits): break
                    v = 0
                    for j in range(cl): v = (v << 1) | bits[bpos + j]
                    if (cl, v) in dd:
                        dist = dd[(cl, v)]; bpos += cl; fd = True; break
                if not fd: raise TransformError("LZH dist")
                fn = False
                for cl in range(1, mnb + 1):
                    if bpos + cl > len(bits): break
                    v = 0
                    for j in range(cl): v = (v << 1) | bits[bpos + j]
                    if (cl, v) in nd:
                        length = nd[(cl, v)]; bpos += cl; fn = True; break
                if not fn: raise TransformError("LZH len")
                tokens.append(('M', dist, length))
        return self._lz77_untokenize(tokens)

    # ---------------- Pipelines ----------------
    def _raw_pipeline(self, data, time_limit=None):
        if time_limit is None: time_limit = self.ULTRA_TIME_LIMIT
        st = time.time()
        best = None; bl = float('inf')
        def try_c(h, t):
            nonlocal best, bl
            c = h + self._compress_backend(t)
            if len(c) < bl: best = c; bl = len(c)
        try_c(self._encode_marker_raw(), data)
        for t in range(1, 257):
            if time_limit and time.time() - st > time_limit: break
            try:
                tr = self.fwd_transforms[t](data)
                if not self._verify_lossless(data, tr, self.rev_transforms[t]): continue
                try_c(self._encode_marker_single(t), tr)
            except Exception: continue
        if best is None: best = self._encode_marker_raw() + self._compress_backend(data)
        d, _ = self._decompress_auto(best)
        if d == data: return best
        return self._encode_marker_raw() + self._compress_backend(data)

    def _lzh_pipeline(self, data, time_limit=None):
        if time_limit is None: time_limit = self.ULTRA_TIME_LIMIT
        st = time.time()
        best = None; bl = float('inf')
        def try_c(h, t):
            nonlocal best, bl
            lzh = self._encode_lzh(t)
            c = h + b'\xFF' + lzh
            if len(c) < bl: best = c; bl = len(c)
        try_c(self._encode_marker_raw(), data)
        for t in range(1, 257):
            if time_limit and time.time() - st > time_limit: break
            try:
                tr = self.fwd_transforms[t](data)
                if not self._verify_lossless(data, tr, self.rev_transforms[t]): continue
                try_c(self._encode_marker_single(t), tr)
            except Exception: continue
        if best is None: best = self._encode_marker_raw() + self._compress_backend(data)
        return best

    def _decompress_auto(self, data):
        off, seq = self._decode_header(data)
        if off == 0: raise DecompressionError("Bad header")
        p = data[off:]
        if not p: raise DecompressionError("Empty")
        r = self._decompress_backend(p)
        if r is None: raise DecompressionError("Backend failed")
        if not seq: return r, None
        return self._reverse_sequence(r, seq), seq

    def _decompress_lzh_pipeline(self, data):
        off, seq = self._decode_header(data)
        if off == 0: return None
        if len(data) <= off or data[off] != 0xFF: return None
        lzh_data = data[off + 1:]
        transformed = self._decode_lzh(lzh_data)
        if transformed is None: return None
        if not seq: return transformed
        return self._reverse_sequence(transformed, seq)

    def _reverse_sequence(self, data, seq):
        r = data
        for t in reversed(seq): r = self.rev_transforms[t](r)
        return r

    # ---------------- SHA-256 wrapper ----------------
    def _wrap_with_hash(self, payload, original):
        return MAGIC + hashlib.sha256(original).digest() + payload
    def _unwrap_and_check(self, blob):
        if not blob.startswith(MAGIC): raise IntegrityError("Not PJP4.")
        if len(blob) < HEADER_LEN: raise IntegrityError("Truncated PJP4.")
        return blob[MAGIC_LEN:HEADER_LEN], blob[HEADER_LEN:]

    # ---------------- File I/O ----------------
    def _atomic_write(self, path, data):
        d = os.path.dirname(path) or '.'
        fd, tmp = tempfile.mkstemp(prefix=os.path.basename(path) + '.tmp', dir=d)
        try: os.write(fd, data); os.fsync(fd)
        finally: os.close(fd)
        os.replace(tmp, path)

    def compress_file_dual(self, infile, time_limit=None):
        try:
            with open(infile, 'rb') as f: data = f.read()
        except Exception as e:
            print(f"Error reading: {e}"); return

        print(f"\nInput: {len(data)} bytes")
        print("=" * 62)
        print("Method A: 256 transforms + PAQ/Zstd/Brotli → .pjp2")
        try: payload_a = self._raw_pipeline(data, time_limit)
        except Exception as e: print(f"  A failed: {e}"); return
        try:
            check_a, _ = self._decompress_auto(payload_a)
        except Exception as e: print(f"  A verify failed: {e}"); return
        if check_a != data: print("  REFUSING A."); return
        print(f"  Size: {len(payload_a)} bytes")

        print("\nMethod B: 256 transforms + LZH + SHA-256 → .pjp3")
        try: payload_b = self._lzh_pipeline(data, time_limit)
        except Exception as e: print(f"  B failed: {e}"); return
        try: check_b = self._decompress_lzh_pipeline(payload_b)
        except Exception as e: print(f"  B verify failed: {e}"); return
        if check_b != data: print("  REFUSING B."); return
        wrapped_b = self._wrap_with_hash(payload_b, data)
        print(f"  Size: {len(wrapped_b)} bytes (with SHA-256)")

        out_a = infile + ".pjp2"
        out_b = infile + ".pjp3"
        try:
            self._atomic_write(out_a, payload_a)
            self._atomic_write(out_b, wrapped_b)
        except Exception as e:
            print(f"Error writing: {e}"); return

        print("\n" + "=" * 62)
        if len(payload_a) <= len(wrapped_b):
            try: os.remove(out_b)
            except Exception: pass
            winner, wsize, loser = out_a, len(payload_a), out_b
        else:
            try: os.remove(out_a)
            except Exception: pass
            winner, wsize, loser = out_b, len(wrapped_b), out_a
        ratio = (wsize / len(data) * 100) if data else 0.0
        print(f"WINNER: {winner}")
        print(f"  {wsize} bytes ({ratio:.2f}%)")
        print(f"DELETED: {loser}")

    def decompress_file(self, infile, outfile=""):
        try:
            with open(infile, 'rb') as f: blob = f.read()
        except Exception as e:
            print(f"Error reading: {e}"); return False

        if blob.startswith(MAGIC):
            print("Format: PJP4 (.pjp3)")
            try: expected_hash, payload = self._unwrap_and_check(blob)
            except IntegrityError as e: print(f"REFUSING: {e}"); return False
            original = None
            try: original = self._decompress_lzh_pipeline(payload)
            except Exception: original = None
            if original is None:
                try: original, _ = self._decompress_auto(payload)
                except Exception as e: print(f"Decompression failed: {e}"); return False
            actual_hash = hashlib.sha256(original).digest()
            if actual_hash != expected_hash:
                print("★★★ INTEGRITY FAILURE ★★★")
                print(f"  Expected: {expected_hash.hex()}")
                print(f"  Actual:   {actual_hash.hex()}")
                return False
            print(f"  SHA-256 verified: {actual_hash.hex()[:32]}…")
        else:
            print("Format: raw payload (.pjp2)")
            try:
                off, seq = self._decode_header(blob)
                if off == 0: print("Bad header"); return False
                if off < len(blob) and blob[off] == 0xFF:
                    original = self._decompress_lzh_pipeline(blob)
                else:
                    original, _ = self._decompress_auto(blob)
            except Exception as e:
                print(f"Decompression failed: {e}"); return False

        if original is None:
            print("Produced None"); return False
        if not outfile:
            base = os.path.basename(infile)
            outfile = re.sub(r'\.pjp[23]?$', '', base)
        try: self._atomic_write(outfile, original)
        except Exception as e:
            print(f"Write failed: {e}"); return False
        print(f"Decompressed → {outfile} ({len(original)} bytes)")
        return True

    def full_self_test(self):
        print("=" * 60); print("Self-Test"); print("=" * 60)
        test_bytes = [0x00, 0xFF, 0xAA, 0x55, 0x12, 0x34]
        all_ok = True
        for t in range(1, 257):
            if t % 50 == 0: print(f"  Testing {t}...")
            for tb in test_bytes:
                d = bytes([tb])
                try:
                    tr = self.fwd_transforms[t](d)
                    rs = self.rev_transforms[t](tr)
                    if rs != d: print(f"  FAIL t={t} b={tb:#04x}"); all_ok = False; break
                except TransformError: continue
                except Exception as e:
                    print(f"  EXC t={t} b={tb:#04x}: {e}"); all_ok = False; break
            if not all_ok: break
        if not all_ok: return False
        print("\n  All 256 transforms passed.")
        rng = random.Random(12345)
        d = bytes(rng.randint(0, 255) for _ in range(256))
        try:
            c = self._raw_pipeline(d, time_limit=60)
            dc, _ = self._decompress_auto(c)
            if dc != d: print("  FAIL raw pipeline"); return False
            print(f"  PASS raw pipeline ({len(d)} → {len(c)})")
        except Exception as e: print(f"  Fail raw: {e}"); return False
        try:
            c = self._lzh_pipeline(d, time_limit=60)
            dc = self._decompress_lzh_pipeline(c)
            if dc != d: print("  FAIL LZH"); return False
            print(f"  PASS LZH ({len(d)} → {len(c)})")
        except Exception as e: print(f"  Fail LZH: {e}"); return False
        print("\nHash wrapper test...")
        try:
            sample = b"hello world"
            wrapped = self._wrap_with_hash(b"PAYLOAD", sample)
            expected, payload = self._unwrap_and_check(wrapped)
            if payload != b"PAYLOAD": raise AssertionError("payload")
            if hashlib.sha256(sample).digest() != expected: raise AssertionError("hash")
            print("  PASS hash wrapper")
        except Exception as e: print(f"  FAIL: {e}"); return False
        print("\n[All checks passed]")
        return True

# ============================ MAIN ============================
def main():
    print(f"{PROGNAME}")
    print("Method A → input.pjp2 (256 transforms + PAQ/Zstd/Brotli)")
    print("Method B → input.pjp3 (256 transforms + LZH + SHA-256)")
    print("Option 1 tries BOTH, keeps SMALLER, deletes the other.\n")

    dl = input("Download 12 dictionaries from Google Drive? (y/n) [y]: ").strip().lower()
    try_download = (dl != 'n')

    c = UnifiedCompressor(try_download=try_download)

    while True:
        print("\nMenu:")
        print("1) Compress (try BOTH, keep smaller)")
        print("2) Decompress (auto-detect)")
        print("3) Full self-test")
        print("0) Exit")
        ch = input("> ").strip()
        if ch == "1":
            f = input("Input file: ").strip()
            c.compress_file_dual(f)
        elif ch == "2":
            while True:
                f = input("Compressed file (.pjp2/.pjp3) [Enter=cancel]: ").strip()
                if not f: break
                if not (f.lower().endswith('.pjp2') or f.lower().endswith('.pjp3')):
                    print("Only .pjp2 / .pjp3 supported."); continue
                o = input("Output file (blank=auto): ").strip()
                if c.decompress_file(f, o): break
                else: print("Try again or Enter to cancel.")
        elif ch == "3":
            c.full_self_test()
        elif ch == "0":
            break
        else:
            print("Invalid.")

if __name__ == "__main__":
    main()
