import os,sys; sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *
from prosodic.langs.finnish import *
from prosodic.langs.english import *
import tempfile
disable_caching()

def test_phonet():
    lang = Language('en')
    
    ipa = lang.get_sylls_ipa_str_tts('dummywummy')
    assert "ˈʌ" in ipa

    sylls1 = lang.syllabify_ipa(ipa)

    osylls_ll = lang.get_sylls_ipa_ll('dummywummy')
    assert osylls_ll
    osylls = osylls_ll[0]
    assert osylls
    sylls2 = osylls[0]

    assert len(sylls2) == 4
    assert sylls1 == sylls2

def test_espeak():
    os.environ['PATH_ESPEAK']=os.environ['PHONEMIZER_ESPEAK_LIBRARY']=''
    with tempfile.TemporaryDirectory() as tdir:
        os.environ['PATH_ESPEAK']=os.environ['PHONEMIZER_ESPEAK_LIBRARY']=''
        with open(os.path.join(tdir,'espeak-ng'),'w', encoding='utf-8') as of: of.write('')
        assert get_espeak_env([tdir]) == tdir
    
    with tempfile.TemporaryDirectory() as tdir:
        os.environ['PATH_ESPEAK']=os.environ['PHONEMIZER_ESPEAK_LIBRARY']=''
        with open(os.path.join(tdir,'espeak-ng'),'w', encoding='utf-8') as of: of.write('')
        assert get_espeak_env([tdir]) == tdir
    
    with tempfile.TemporaryDirectory() as tdir:
        opath=os.path.join(tdir,'a','b','b')
        os.makedirs(opath,exist_ok=True)
        lib_fn='libespeak.dylib'
        with open(os.path.join(opath,lib_fn),'w', encoding='utf-8') as of: of.write('')
        assert get_espeak_env([tdir]) == os.path.join(opath,lib_fn)

    with tempfile.TemporaryDirectory() as tdir:
        opath=os.path.join(tdir,'a','b','c')
        os.makedirs(opath,exist_ok=True)
        lib_fn='libespeak.so'
        with open(os.path.join(opath,lib_fn),'w', encoding='utf-8') as of: of.write('')
        assert get_espeak_env([tdir]) == os.path.join(opath,lib_fn)

    os.environ['PATH_ESPEAK']= 'hello'
    assert get_espeak_env([]) == os.environ['PATH_ESPEAK']

    os.environ['PATH_ESPEAK']=os.environ['PHONEMIZER_ESPEAK_LIBRARY']=''
    set_espeak_env()



finnish_words = """kuin minä hänen että hän oli varten päälle olemme kanssa ne olla klo yksi olla tämä alkaen mukaan kuuma sana mutta mitä jotkut on se sinua tai oli päälle jos to ja tehdä sisään me voida ulos muut olivat joka tehdä niiden aika jos tahtoa miten sanoi pieni kukin kertoa tekee setti kolme haluta ilma hyvin myös pelata pieni pää laittaa koti lue käsi portti suuri oikeinkirjoituksen lisätä jopa maa täällä must iso korkea niin seurata säädös miksi kysyä miehet muutos meni valo kind pois tarvitsevat talo kuva yrittää meille jälleen eläin kohta äiti maailma lähellä rakentaa itse maa isä kaikki uusi työ osa ottaa saada paikka tehty elää jossa jälkeen takaisin vähän vain pyöreä mies vuosi tuli show joka hyvä minua antaa meidän alle nimi hyvin kautta vain lomake virke suuri ajatella sanoa auttaa alhainen linja erota vuoro syy paljon tarkoittaa ennen liikkua oikea poika vanha liian sama hän kaikki siellä kun ylös käyttää sinun tapa noin monet sitten niitä kirjoittaa olisi kuten niin nämä hänen pitkä tehdä asia nähdä häntä kaksi on katso lisää päivä voisi mennä tulevat teki numero ääni ei eniten ihmiset minun yli tietää vesi kuin puhelu ensimmäinen jotka saattaa alas puoli ollut nyt löytää pää seistä oma sivu pitäisi maa löytyi vastaus koulu kasvaa tutkimus vielä oppia kasvi kansi ruoka aurinko neljä välillä valtio pitää silmä ei koskaan viime antaa ajatus kaupunki puu cross maatila kova alku ehkä tarina saha pitkälle meri piirtää vasen myöhään run eivät taas lehdistö lähellä yö todellinen elämä harvat pohjoiseen kirja kuljettaa otti tiede syödä huone ystävä alkoi idea kala vuori lopettaa kerran pohja kuulla hevonen leikkaus varma katsella väri kasvot puu tärkein avoin näyttää yhdessä seuraava valkoinen lapset alkaa sai kävellä esimerkiksi helppous paperi ryhmä aina musiikki ne molemmat merkki usein kirje saakka maili joki auto jalat hoito toinen tarpeeksi tavallinen tyttö tavallinen nuori valmis edellä koskaan punainen lista vaikka tuntea puhua lintu pian elin koira perhe suora aiheuttaa jätä laulu mitata ovi tuote musta lyhyt numero luokka tuuli kysymys tapahtua täydellinen laiva alue puoli kallio järjestys palo etelään ongelma pala kertoi tiesi kulkea koska alkuun koko kuningas katu tuuma lisääntyä ei mitään kurssi pysyä pyörä täysi voima sininen esine päättää pinta syvä moon saari jalka järjestelmä kiireinen testi ennätys veneen yhteinen kulta mahdollinen kone sijaansa kuiva ihme nauraa tuhatta sitten juoksi tarkistaa peli muoto rinnastaa kuuma neiti toi lämpö lumi rengas tuoda kyllä kaukainen täyttää itään maali kieli keskuudessa yksikkö voima kaupunki hieno tietty lentää pudota johtaa itkeä pimeä kone huomautus odottaa suunnitelma kuva tähti laatikko substantiivi kenttä levätä oikea pystyy punta tehty kauneus ajaa seisoi sisältävät etuosa opettaa viikko lopullinen antoi vihreä oi nopea kehittää valtameri lämmin vapaa minuutti vahva erityistä mieli takana selkeä pyrstö tuottaa tosiasia tilaa kuuli paras tunti parempi totta aikana sata viisi muistaa vaihe varhainen pidä länsi maa etua tavoittaa nopeasti verbi laulaa kuunnella kuusi taulukko matkailu vähemmän aamu kymmenen yksinkertainen useat vokaali kohti sota asettaa vastaan kuvio hidas keskus rakkaus henkilö raha palvella ilmestyä tie kartta sade sääntö säätelevät vetää kylmä huomautus ääni energia metsästää todennäköinen sängyssä veli muna ratsastaa solu uskoa ehkä poimia äkillinen luottaa neliö syy pituus edustaa taide aihe alue koko vaihdella asettua puhua paino yleinen jää asia ympyrä pari sisältävät kahtiajaon tavu huopa suuri pallo vielä aalto pudota sydän am nykyinen raskas tanssi moottori asema varsi leveä purje materiaali osa metsä istua kilpailu ikkuna myymälä kesä juna uni todistaa yksinäinen jalka liikunta seinä saalis mount toivottaa taivas lauta ilo talvi kyll kirjallinen villi väline säilytettävä lasi ruoho lehmä työ reuna merkki Vierailun ohi pehmeä hauskaa kirkas kaasu sää kuukausi miljoona bear viimeistely onnellinen Toivottavasti kukka vaatettaa outo poissa kauppa melodia matka toimisto vastaanottaa rivi suu tarkka symboli die vähiten ongelmia huutaa paitsi kirjoitti siemen sävy yhtyä ehdottaa puhtaita tauko lady piha nousta huono puhallus öljy veri koskettaa kasvoi sentti sekoittaa joukkue lanka kustannukset menetetty ruskea kuluminen puutarha yhtäläinen lähetetty valita laski sovittaa virtaus oikeudenmukainen pankki kerätä tallentaa ohjaus desimaalin korva muu melko rikkoi asia keskellä tappaa poika järvi hetki asteikko äänekäs kevät tarkkailla lapsi suora konsonantti kansakunta sanakirja maito nopeus menetelmä urut maksaa ikä jakso mekko pilvi yllätys hiljainen kivi pikkuruinen kiivetä viileä suunnittelu kehno paljon kokeilu pohja avain rauta single stick tasainen kaksikymmentä iho hymy prässi reikä hyppy vauva kahdeksan kylä tavata juuri ostaa nostaa ratkaista metalli onko push seitsemän kohta kolmas on held hiukset kuvata kokki lattia jompikumpi tulos polttaa mäki turvallinen kissa luvulla harkita tyyppi laki bitti rannikolla kopio lause hiljainen pitkä hiekka maaperä rulla lämpötila sormi teollisuus arvo taistelu valhe voittaa kiihottaa luonnollinen näkymä merkityksessä pääoma eivät tuoli vaara hedelmät rikas paksu sotilas prosessi toimivat käytäntö erillinen vaikea lääkäri olkaa hyvä suojella keskipäivällä kasvuston nykyaikainen elementti osuma opiskelija kulma puolue tarjonta joiden paikantaa rengas merkki hyönteinen kiinni aika osoittaa radio puhui atomi ihmisen historia vaikutus sähköinen odottaa luu kisko kuvitella antaa suostua näin lempeä nainen kapteeni arvata välttämätön teräviä siipi luoda naapuri pesu lepakko pikemminkin väkijoukko maissi vertaa runo string soittokello riippua liha hieroa putki kuuluisa dollari virta pelko näky ohut kolmio planeetta kiire päällikkö siirtomaa kello mine sitoa astua merkittävä tuore haku lähettää keltainen gun sallia painatus kuollut paikka aavikko puku nykyinen hissi Rose saapua mestari raita vanhempi rannikko jako arkki aine suosia kytkeä virka viettää sointu rasva iloinen alkuperäinen osake asema isä leipä veloittaa oikea bar tarjous segmentti orja ankka välitön markkinat aste asuttaa poikasen rakas vihollinen vastata juoma esiintyä tuki puhe luonto alue höyry motion polku neste loki tarkoitti osamäärä hampaat kuori niska happi sokeri kuolema aika taito naiset kausi ratkaisu magneetti hopea kiitos sivuliike ottelu pääte erityisesti viikuna peloissaan valtava sisko teräs keskustella eteenpäin samankaltainen opas kokemus pisteet omena ostivat led piki takki massa kortti bändi köysi lipsahdus voittaa unelma ilta ehto rehu työkalu yhteensä perus haju laakso eikä myöskään kaksinkertainen istuin jatkaa lohko kaavio hattu myydä menestys yritys vähentää tapahtuma erityinen sopimus uida termi päinvastainen vaimo kenkä olkapää leviäminen järjestää leiri keksiä puuvilla Born määrittää gallona yhdeksän truck melu taso mahdollisuus kerätä kauppa venyttää heittää paistaa omaisuus sarake molekyyli valita väärä harmaa toistaa vaatia laaja valmistella suola nenä monikko viha vaatimus maanosa""".split()


def test_finnish():
    
    assert isinstance(Language('fi'), FinnishLanguage)
    wtype = Word('kalevala',lang='fi')
    assert wtype.is_wordtype
    assert len(wtype.wordforms)==1
    assert len(wtype.syllables)==4
    assert wtype.wordforms[0].num_stressed_sylls == 2

    for w in tqdm(finnish_words,position=0):
        wtype = Word(w, lang='fi')
        assert wtype.wordforms
        assert wtype.syllables
        assert wtype.phonemes





english_words="""a ability able about above accept according account across act action activity actually add address administration admit adult affect after again against age agency agent ago agree agreement ahead air all allow almost alone along already also although always American among amount analysis and animal another answer any anyone anything appear apply approach area argue arm around arrive art article artist as ask assume at attack attention attorney audience author authority available avoid away baby back bad bag ball bank bar base be beat beautiful because become bed before begin behavior behind believe benefit best better between beyond big bill billion bit black blood blue board body book born both box boy break bring brother budget build building business but buy by call camera campaign can cancer candidate capital car card care career carry case catch cause cell center central century certain certainly chair challenge chance change character charge check child choice choose church citizen city civil claim class clear clearly close coach cold collection college color come commercial common community company compare computer concern condition conference Congress consider consumer contain continue control cost could country couple course court cover create crime cultural culture cup current customer cut dark data daughter day dead deal death debate decade decide decision deep defense degree Democrat democratic describe design despite detail determine develop development die difference different difficult dinner direction director discover discuss discussion disease do doctor dog door down draw dream drive drop drug during each early east easy eat economic economy edge education effect effort eight either election else employee end energy enjoy enough enter entire environment environmental especially establish even evening event ever every everybody everyone everything evidence exactly example executive exist expect experience expert explain eye face fact factor fail fall family far fast father fear federal feel feeling few field fight figure fill film final finally financial find fine finger finish fire firm first fish five floor fly focus follow food foot for force foreign forget form former forward four free friend from front full fund future game garden gas general generation get girl give glass go goal good government great green ground group grow growth guess gun guy hair half hand hang happen happy hard have he head health hear heart heat heavy help her here herself high him himself his history hit hold home hope hospital hot hotel hour house how however huge human hundred husband I idea identify if image imagine impact important improve in include including increase indeed indicate individual industry information inside instead institution interest interesting international interview into investment involve issue it item its itself job join just keep key kid kill kind kitchen know knowledge land language large last late later laugh law lawyer lay lead leader learn least leave left leg legal less let letter level lie life light like likely line list listen little live local long look lose loss lot love low machine magazine main maintain major majority make man manage management manager many market marriage material matter may maybe me mean measure media medical meet meeting member memory mention message method middle might military million mind minute miss mission model modern moment money month more morning most mother mouth move movement movie Mr Mrs much music must my myself name nation national natural nature near nearly necessary need network never new news newspaper next nice night no none nor north not note nothing notice now n't number occur of off offer office officer official often oh oil ok old on once one only onto open operation opportunity option or order organization other others our out outside over own owner page pain painting paper parent part participant particular particularly partner party pass past patient pattern pay peace people per perform performance perhaps period person personal phone physical pick picture piece place plan plant play player PM point police policy political politics poor popular population position positive possible power practice prepare present president pressure pretty prevent price private probably problem process produce product production professional professor program project property protect prove provide public pull purpose push put quality question quickly quite race radio raise range rate rather reach read ready real reality realize really reason receive recent recently recognize record red reduce reflect region relate relationship religious remain remember remove report represent Republican require research resource respond response responsibility rest result return reveal rich right rise risk road rock role room rule run safe same save say scene school science scientist score sea season seat second section security see seek seem sell send senior sense series serious serve service set seven several sex sexual shake share she shoot short shot should shoulder show side sign significant similar simple simply since sing single sister sit site situation six size skill skin small smile so social society soldier some somebody someone something sometimes son song soon sort sound source south southern space speak special specific speech spend sport spring staff stage stand standard star start state statement station stay step still stock stop store story strategy street strong structure student study stuff style subject success successful such suddenly suffer suggest summer support sure surface system table take talk task tax teach teacher team technology television tell ten tend term test than thank that the their them themselves then theory there these they thing think third this those though thought thousand threat three through throughout throw thus time to today together tonight too top total tough toward town trade traditional training travel treat treatment tree trial trip trouble true truth try turn TV two type under understand unit until up upon us use usually value various very victim view violence visit voice vote wait walk wall want war watch water way we weapon wear week weight well west western what whatever when where whether which while white who whole whom whose why wide wife will win wind window wish with within without woman wonder word work worker world worry would write writer wrong yard yeah year yes yet you young your yourself""".split()

def test_english():
    for w in tqdm(english_words,position=0):
        wtype = Word(w, lang='en')
        assert wtype.wordforms
        assert wtype.syllables
        assert wtype.phonemes

def test_normalize_espeak_ipa():
    """The normalizer fixes IPA tokens that panphon's ipa_segs drops
    or that espeak bundles into one token but span two syllables."""
    from prosodic.langs.langs import _normalize_espeak_ipa
    # silent-drop class: ɚ, ɝ, ᵻ
    assert _normalize_espeak_ipa("ɹ ˈaɪ p ɚ") == "ɹ ˈaɪ p ə ɹ"
    assert _normalize_espeak_ipa("ɹ ˈoʊ z ᵻ z") == "ɹ ˈoʊ z ɪ z"
    assert _normalize_espeak_ipa("b ɝ d") == "b ˈə ɹ d"
    # hiatus-class: aɪə, iə and their stress variants
    assert _normalize_espeak_ipa("s ˈaɪə n s") == "s ˈaɪ ə n s"
    assert _normalize_espeak_ipa("m æ m ˈeɪ l iə n") == "m æ m ˈeɪ l i ə n"
    # idempotent
    clean = "t ˈɛ s t"
    assert _normalize_espeak_ipa(clean) == clean


def test_syllabify_known_bugs():
    """Regression tests for words that used to syllabify incorrectly
    due to panphon/espeak/syllabiphon interactions."""
    lang = Language('en')
    # r-colored schwa: riper must be 2 sylls with ˈɹaɪ.pəɹ
    sylls = lang.get_sylls_ipa_l_tts('riper')
    assert len(sylls) == 2, f"riper should be disyllabic, got {sylls}"
    assert "ɹ" in sylls[1], f"riper's final syllable should contain ɹ, got {sylls}"
    assert "ə" in sylls[1]
    # deeper, super: ɚ used to be dropped entirely (1 syll, no ɹ)
    for w in ['deeper', 'super', 'teacher', 'mother', 'over']:
        s = lang.get_sylls_ipa_l_tts(w)
        assert len(s) == 2, f"{w}: expected 2 sylls, got {s}"
        assert "ɹ" in s[-1], f"{w}: final syll should contain ɹ, got {s}"
    # ᵻ (barred-i): these used to lose their final consonant too
    for w, expected_n in [('roses', 2), ('hunted', 2), ('wanted', 2), ('wishes', 2)]:
        s = lang.get_sylls_ipa_l_tts(w)
        assert len(s) == expected_n, f"{w}: expected {expected_n} sylls, got {s}"
    # hiatus: aɪə / iə used to collapse to one syll
    for w, expected_n in [('science', 2), ('zion', 2), ('lion', 2), ('quiet', 2),
                           ('defiance', 3), ('prescient', 3)]:
        s = lang.get_sylls_ipa_l_tts(w)
        assert len(s) == expected_n, f"{w}: expected {expected_n} sylls, got {s}"


def test_no_silent_ipa_drops():
    """For a set of common words, no phn token emitted by espeak should
    vanish at the panphon stage. This is the invariant violated by ɚ/ɝ/ᵻ
    (and any future such symbol)."""
    from prosodic.lib.syllabiphon.syllabify import Syllabify
    lang = Language('en')
    syl = Syllabify()
    # Variety: plurals (ᵻ), -er words (ɚ), hiatus (aɪə/iə), stress
    probe = ['teacher', 'riper', 'roses', 'hunted', 'wishes', 'science',
             'zion', 'quiet', 'media', 'serial', 'inhabited', 'convinces',
             'differences', 'bird', 'mother', 'river', 'never']
    for w in probe:
        ipa = lang.get_sylls_ipa_str_tts(w)
        phns = ipa.split()
        # every phn must contribute at least one segment to panphon's segs
        for p in phns:
            pc = p.replace('ˈ', '').replace('ˌ', '')
            segs = syl.ft.ipa_segs(pc)
            assert segs, (
                f"word={w!r} ipa={ipa!r}: phn {p!r} is invisible to panphon "
                f"(no ipa_segs) — this is the class of bug that loses sylls"
            )


def test_espeak_vs_cmu_agreement():
    """Benchmark: for common English words that have a single CMU
    pronunciation, the espeak+panphon+syllabify path should agree with
    CMU on syllable count and stress position. The floor values below
    are set with margin under the observed baseline so real regressions
    (e.g., a new silent-drop symbol) fire this test."""
    from collections import defaultdict
    lang = Language('en')
    # load CMU dict, keep words with exactly one pronunciation
    all_ent = defaultdict(list)
    cmu_path = os.path.join(
        os.path.dirname(__file__), '..', 'prosodic', 'langs', 'english',
        'english.tsv',
    )
    with open(cmu_path, encoding='utf-8') as f:
        for ln in f:
            ln = ln.strip()
            if not ln or '\t' not in ln: continue
            w, ipa = ln.split('\t', 1)
            all_ent[w.lower()].append(ipa)

    def stress_pos(sylls):
        for i, s in enumerate(sylls):
            if "'" in s or 'ˈ' in s: return i
        return -1

    syll_ok = stress_ok = tested = 0
    disagreements = []
    for w in english_words:
        wl = w.lower()
        ipas = all_ent.get(wl, [])
        if len(ipas) != 1:
            continue
        cmu_sylls = ipas[0].split('.')
        esp_sylls = lang.get_sylls_ipa_l_tts(wl)
        if not esp_sylls:
            continue
        tested += 1
        if len(cmu_sylls) == len(esp_sylls):
            syll_ok += 1
        else:
            disagreements.append((wl, cmu_sylls, esp_sylls))
        if stress_pos(cmu_sylls) == stress_pos(esp_sylls):
            stress_ok += 1

    assert tested >= 800, f"too few words tested: {tested}"
    syll_pct = syll_ok / tested * 100
    stress_pct = stress_ok / tested * 100
    # set floor below baseline (97.8% / 97.4% as of r-colored-schwa fix)
    assert syll_pct >= 95.0, (
        f"espeak vs CMU syll-count agreement dropped to {syll_pct:.1f}% "
        f"(was 97.8%). First 10 disagreements: {disagreements[:10]}"
    )
    assert stress_pct >= 95.0, (
        f"espeak vs CMU stress-position agreement dropped to {stress_pct:.1f}% "
        f"(was 97.4%)"
    )


def test_every_syllable_has_a_vowel():
    """Every syllable the tokenizer produces should have a vowel nucleus.
    A vowel-less syllable is a symptom of alignment drift between phns and segs."""
    from prosodic.words import Phoneme
    lang = Language('en')
    probe = ['teacher', 'riper', 'roses', 'hunted', 'wishes', 'science',
             'zion', 'defiance', 'media', 'serial', 'mammalian', 'ironwork',
             'inhabited', 'immaterial']
    for w in probe:
        sylls = lang.get_sylls_ipa_l_tts(w)
        assert sylls, f"{w}: no syllables produced"
        for i, s in enumerate(sylls):
            clean = s.replace("'", "").replace("`", "")
            has_vowel = any(
                Phoneme(txt=ch).is_vowel is True for ch in clean if ch.isalpha()
            )
            assert has_vowel, (
                f"{w}: syll {i} ({s!r}) has no vowel nucleus — sylls={sylls}"
            )


def test_tts_cache_dedup_on_load(tmp_path):
    """A user-local TTS cache that accumulated duplicate rows (across runs or
    parallel processes) collapses to one entry per (token, pronunciation) on
    load, keeping distinct pronunciation variants -- and the file is rewritten
    without the dupes so it does not grow unbounded."""
    from prosodic.langs.langs import LanguageModel
    cache_file = tmp_path / "en_cache.tsv"
    cache_file.write_text(
        "foobarbaz\t'fu.baɹ.baz\n"
        "foobarbaz\t'fu.baɹ.baz\n"   # exact duplicate -> collapse
        "foobarbaz\tfu.'baɹ.baz\n"   # distinct variant  -> keep
        "quuxword\t'kwʌks\n"
        "quuxword\t'kwʌks\n",        # exact duplicate -> collapse
        encoding="utf-8",
    )

    class _CacheLang(LanguageModel):
        # name=None -> no main dictionary; only the cache below is loaded
        @property
        def path_token2ipa_cache(self):
            return str(cache_file)

    lang = _CacheLang()
    d = lang.token2ipa
    # exact-duplicate rows collapsed, distinct variant retained
    assert d["foobarbaz"] == [["'fu", "baɹ", "baz"], ["fu", "'baɹ", "baz"]]
    assert d["quuxword"] == [["'kwʌks"]]
    # the on-disk cache was rewritten without the duplicate rows
    lines = [l for l in cache_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 3
    assert lines.count("quuxword\t'kwʌks") == 1
    assert lines.count("foobarbaz\t'fu.baɹ.baz") == 1


def test_tts_hit_updates_inmemory_map_single_espeak(tmp_path):
    """After a TTS (espeak) hit, the pronunciation is inserted into the
    in-memory map, so a second lookup of the same token this session -- even
    with a different force arg (a distinct get_sylls_ipa_ll cache key) -- is
    served from the dict and does NOT re-invoke the TTS/espeak path."""
    from prosodic.langs.langs import LanguageModel
    cache_file = tmp_path / "english_cache.tsv"

    class _CountingLang(LanguageModel):
        def __init__(self, cache_path):
            self._cache_path = cache_path
            self.tts_calls = 0

        @property
        def path_token2ipa_cache(self):
            return self._cache_path

        # stand in for the espeak/TTS path (get_sylls_ipa_ll_tts is what would
        # invoke the phonemizer); count invocations, return a canned result.
        def get_sylls_ipa_ll_tts(self, token):
            self.tts_calls += 1
            return [["'hɛ", "loʊ"]]

    lang = _CountingLang(str(cache_file))

    r1 = lang.get_sylls_ipa_ll("helloword")
    assert r1
    assert lang.tts_calls == 1
    # the token is now in the in-memory map...
    assert "helloword" in lang.token2ipa
    assert lang.get_sylls_ipa_ll_dict("helloword")
    # ...and written to disk for the next session
    assert cache_file.exists()

    # second lookup with a DIFFERENT force arg -> distinct lru_cache key, so the
    # method body runs again, but it must resolve from the dict, not re-TTS.
    r2 = lang.get_sylls_ipa_ll("helloword", force_unstress=True)
    assert r2
    assert lang.tts_calls == 1


def test_stresses():
    # Test sylls_ipa_l_has_stress
    assert sylls_ipa_l_has_stress(["'maɪ"])
    assert not sylls_ipa_l_has_stress(["maɪ"])
    
    # Test sylls_ipa_l_is_unstressed
    assert sylls_ipa_l_is_unstressed(["maɪ"])
    assert not sylls_ipa_l_is_unstressed(["'maɪ"])
    
    # Test sylls_ipa_ll_has_stress
    assert sylls_ipa_ll_has_stress([["'maɪ"], ["maɪ"]])
    assert not sylls_ipa_ll_has_stress([["maɪ"], ["maɪ"]])
    
    # Test sylls_ipa_ll_has_unstress
    assert sylls_ipa_ll_has_unstress([["'maɪ"], ["maɪ"]])
    assert not sylls_ipa_ll_has_unstress([["'maɪ"], ["'maɪ"]])
    
    # Test sylls_ipa_ll_has_ambig_stress
    assert sylls_ipa_ll_has_ambig_stress([["'maɪ"], ["maɪ"]])
    assert not sylls_ipa_ll_has_ambig_stress([["'maɪ"], ["'maɪ"]])
    
    # Test unstress_sylls_ipa_l
    assert unstress_sylls_ipa_l(["'maɪ", "`naɪs"]) == ["maɪ", "naɪs"]

    # Test get_sylls_ll
    sylls_ipa_ll = [["'maɪ"], ["naɪs"]]
    sylls_text_ll = [["my"], ["nice"]]
    expected_result = [[("'maɪ", "my")], [("naɪs", "nice")]]
    assert get_sylls_ll(sylls_ipa_ll, sylls_text_ll) == expected_result


def test_syllabify_ipa_token_seg_alignment():
    """Diphthongs ('aʊ') and affricates ('dʒ') are ONE espeak token but TWO
    panphon segs; boundary flags must be consumed per-token. The old naive
    zip shifted every boundary after the first such token (deterministic:
    raw IPA in, no espeak needed)."""
    en = Language('en')
    # diphthong then later syllables: shift would corrupt the whole tail
    assert len(en.syllabify_ipa("p ˈaɪ ɹ ə t")) == 2       # pirate
    assert len(en.syllabify_ipa("d ˈaʊ n w ə ɹ d")) == 2   # downward
    assert len(en.syllabify_ipa("tʃ ˈɪɹ f ə l")) == 2      # chearful
    # boundary flagged on the second half of an affricate must still split
    assert len(en.syllabify_ipa("ˈɛ n dʒ ɪ n")) == 2       # engine
    # two adjacent vowel tokens are two nuclei -> forced boundary
    assert len(en.syllabify_ipa("ɡ ˈeɪ ə s t")) == 2       # gayest
    assert len(en.syllabify_ipa("f ˈaɪ ə ɹ")) == 2         # fire
    # German-style secondary-stressed hiatus after a diphthong+cluster
    assert len(en.syllabify_ipa("ˈaʊ f ʃ t ˌeː ə n")) == 3  # aufstehen


# ---------------------------------------------------------------------------
# LanguageModel pronunciation-layer internals (langs.py coverage)
# ---------------------------------------------------------------------------
from prosodic.langs import langs as _lm
from prosodic.langs.langs import (
    LanguageModel,
    Language,
    get_word,
    fix_num_sylls,
    unstress,
    stress,
    stress_sylls_ipa_l,
    syll_ipa_str_is_unstressed,
    sylls_ipa_l_has_unstress,
    get_espeak_error_msg,
    get_espeak_env,
)


def test_getitem_delegates_to_get():
    """LanguageModel.__getitem__ is sugar for .get() (line 44)."""
    lang = EnglishLanguage()
    got = lang["with"]
    assert got == lang.get("with")
    # get_sylls_ll payload: one pronunciation, one (ipa, text) syllable pair
    assert got[0] == [[("wɪð", "with")]]


def test_ipa_origin_dict_vs_tts(tmp_path):
    """A CMU-dictionary word reports ipa_origin='dict'; a nonce word falls back
    to espeak/TTS (ipa_origin='tts', line 333), the raw pronunciation is written
    to the user-local cache (lines 258-269), and the in-memory map is updated so
    a repeat lookup this session resolves from the dict."""

    class _TmpCacheEnglish(EnglishLanguage):
        @property
        def path_token2ipa_cache(self):
            return str(tmp_path / "english_cache.tsv")

    lang = _TmpCacheEnglish()
    # dictionary hit
    _, meta = lang.get_sylls_ipa_ll("with")
    assert meta["ipa_origin"] == "dict"
    # espeak fallback for a word absent from CMU
    ll, meta = lang.get_sylls_ipa_ll("zzblorptx")
    assert meta["ipa_origin"] == "tts"
    assert ll and ll[0]
    cache = tmp_path / "english_cache.tsv"
    assert cache.exists()
    assert "zzblorptx" in cache.read_text(encoding="utf-8")
    # second lookup (different force arg -> distinct cache key) resolves 'dict',
    # not a re-run of espeak, because the in-memory map was updated
    _, meta2 = lang.get_sylls_ipa_ll("zzblorptx", force_unstress=True)
    assert meta2["ipa_origin"] == "dict"


def test_ipa_origin_error_when_tts_empty(tmp_path):
    """If neither the dictionary nor TTS yields a pronunciation, ipa_origin is
    'error' and an empty parse is returned (lines 270-272)."""

    class _NoTTS(EnglishLanguage):
        @property
        def path_token2ipa_cache(self):
            return str(tmp_path / "c.tsv")

        def get_sylls_ipa_ll_tts(self, token):
            return []

    ll, meta = _NoTTS().get_sylls_ipa_ll("zznovowelq")
    assert meta["ipa_origin"] == "error"
    assert ll == []


def test_trailing_apostrophe_strip_on_miss():
    """A bare trailing apostrophe survives tokenization; the lookup tries the
    original token first, then strips the apostrophe ONLY on a dict miss
    (line 251) -- while genuine apostrophe-final CMU keys hit directly."""
    lang = EnglishLanguage()
    # that' -> misses "that'", falls back to "that" (an ambig-stress entry:
    # unstressed + stressed = 2 forms), origin still 'dict'
    ll, meta = lang.get_sylls_ipa_ll("that'")
    assert meta["ipa_origin"] == "dict"
    assert len(ll) == 2
    assert ll == lang.get_sylls_ipa_ll("that")[0]
    # augustus' -> strips to "augustus"; CMU stress is a-GUS-tus (2nd syllable)
    ll, meta = lang.get_sylls_ipa_ll("augustus'")
    assert meta["ipa_origin"] == "dict"
    assert len(ll) == 1
    stressed = [i for i, s in enumerate(ll[0]) if s[:1] in ("'", "`")]
    assert stressed == [1], f"augustus' should stress syll 1, got {ll[0]}"
    # runnin' -> a genuine CMU key ending in apostrophe: hit directly, NOT stripped
    ll, meta = lang.get_sylls_ipa_ll("runnin'")
    assert meta["ipa_origin"] == "dict"
    assert len(ll[0]) == 2  # run-nin


def test_elision_wiring_flower_fire_heaven():
    """With EnglishLanguage.use_elision on, get_sylls_ipa_ll adds a reduced-
    syllable variant alongside the full pronunciation (lines 283-290); the base
    LanguageModel elides nothing (line 201)."""
    lang = EnglishLanguage()
    assert lang.use_elision is True
    for w in ("flower", "fire", "heaven"):
        ll, _ = lang.get_sylls_ipa_ll(w)
        lens = sorted(len(x) for x in ll)
        assert lens == [1, 2], f"{w}: expected 1-syll elision + 2-syll base, got {ll}"
    # get_elided_pronunciations directly: fire ('faɪ.ɛː -> 'faɪr)
    assert lang.get_elided_pronunciations(["'faɪ", "ɛː"]) == [["'faɪr"]]
    # base language elides nothing
    assert LanguageModel().get_elided_pronunciations(["'faɪ", "ɛː"]) == []


def test_force_ambig_stress_synthesizes_missing_polarity():
    """force_ambig_stress adds whichever stress polarity is missing: a stressed
    variant when the pronunciation is unstressed-only (line 299) and an
    unstressed variant when it is stressed-only (line 301)."""

    class _UnstrOnly(LanguageModel):
        def get_sylls_ipa_ll_dict(self, token):
            return [["bə"]]

    ll, _ = _UnstrOnly().get_sylls_ipa_ll("x", force_ambig_stress=True)
    assert sorted(ll) == [["'bə"], ["bə"]]

    class _StrOnly(LanguageModel):
        def get_sylls_ipa_ll_dict(self, token):
            return [["'bə"]]

    ll, _ = _StrOnly().get_sylls_ipa_ll("x", force_ambig_stress=True)
    assert sorted(ll) == [["'bə"], ["bə"]]


def test_ambig_and_unstress_membership():
    """Membership drives forcing: 'the' is unstressed-only; 'she' is in BOTH
    lists, so ambiguous-stress wins (2 forms, can bear a beat)."""
    lang = EnglishLanguage()
    assert "the" in lang.unstressed_words
    assert "she" in lang.ambig_stressed_words and "she" in lang.unstressed_words
    _, meta = lang.get_sylls_ipa_ll("the")
    assert meta["force_unstress"] is True and meta["force_ambig_stress"] is None
    ll, meta = lang.get_sylls_ipa_ll("she")
    assert meta["force_ambig_stress"] is True
    assert len(ll) == 2  # stressed + unstressed


def test_base_language_defaults():
    """The base LanguageModel (no name) has empty membership sets, a null TTS
    cache path (line 90), and inert rule/cache hooks (lines 148, 185, 195)."""
    b = LanguageModel()
    assert b.name is None
    assert b.path_token2ipa_cache is None
    assert b.unstressed_words == set()
    assert b.ambig_stressed_words == set()
    assert b.get_sylls_ipa_ll_rule("x") == ([], {})
    assert b.get_sylls_ll_rule("x") == ([], {})
    # best-effort disk hooks no-op when there is no cache path
    b._dedupe_cache_file()
    b._cache_tts_result("foo", ["'fu"])


def test_load_token2ipa_file_direct(tmp_path):
    """_load_token2ipa_file defaults its accumulators (lines 116, 118) and skips
    exact-duplicate (token, pronunciation) rows while keeping distinct
    pronunciation variants (line 129)."""
    p = tmp_path / "dict.tsv"
    p.write_text(
        "cat\t'kæt\n"
        "cat\t'kæt\n"   # exact duplicate -> skipped
        "cat\tk.'æt\n"  # distinct variant -> kept
        "dog\t'dɔɡ\n"
        "notabhere\n"   # no separator -> ignored
        "\n",           # blank -> ignored
        encoding="utf-8",
    )
    d = LanguageModel()._load_token2ipa_file(str(p))
    assert d["cat"] == [["'kæt"], ["k", "'æt"]]
    assert d["dog"] == [["'dɔɡ"]]
    assert "notabhere" not in d


def test_stress_helper_functions():
    """Small IPA stress utilities (lines 518, 525-529, 533, 549, 553)."""
    assert unstress("") == ""
    assert unstress("'maɪ") == "maɪ"
    assert stress("") == ""
    assert stress("maɪ") == "'maɪ"
    assert stress("maɪ", primary=False) == "`maɪ"
    assert stress("'maɪ") == "'maɪ"  # already stressed -> normalized, re-marked
    assert stress_sylls_ipa_l(["maɪ", "naɪs"]) == ["'maɪ", "`naɪs"]
    assert syll_ipa_str_is_unstressed("maɪ") is True
    assert syll_ipa_str_is_unstressed("'maɪ") is False
    assert sylls_ipa_l_has_unstress(["'maɪ", "naɪs"]) is True
    assert sylls_ipa_l_has_unstress(["'maɪ"]) is False


def test_fix_num_sylls_shrink_and_grow():
    """fix_num_sylls merges when there are too many syllables (lines 508-509)
    and splits when there are too few; empty pieces become '?'."""
    assert fix_num_sylls(["a", "b", "c"], 2) == ["a", "bc"]
    assert fix_num_sylls(["abcd"], 2) == ["ab", "cd"]
    assert fix_num_sylls([""], 1) == ["?"]


def test_get_espeak_error_msg_lists_paths():
    """The espeak-not-found message names espeak and echoes the searched
    paths (lines 593-594)."""
    msg = get_espeak_error_msg(["/opt/none", "/usr/none"])
    assert "espeak" in msg.lower()
    assert "/opt/none" in msg and "/usr/none" in msg


def test_glob_espeak_lib(tmp_path):
    """_glob_espeak_lib prefers an unversioned filename, else falls back to the
    first sorted match, and returns '' when nothing matches (lines 675-686)."""
    (tmp_path / "libespeak.dylib").write_text("")
    (tmp_path / "libespeak.so.1").write_text("")
    pat = str(tmp_path / "libespeak*")
    # preferred (unversioned) name wins even though .so.1 also matches
    assert _lm._glob_espeak_lib(globs=[pat], preferred={"libespeak.dylib"}) == str(
        tmp_path / "libespeak.dylib"
    )
    # no preferred match -> first in sorted order (libespeak.dylib < libespeak.so.1)
    assert _lm._glob_espeak_lib(globs=[pat], preferred={"nope"}) == str(
        tmp_path / "libespeak.dylib"
    )
    # nothing matches -> ''
    assert _lm._glob_espeak_lib(globs=[str(tmp_path / "zzz*")], preferred=set()) == ""


def test_find_espeak_lib_recursive_skips(tmp_path):
    """_find_espeak_lib_recursive skips non-directories (700) and broad system
    dirs (702), returns '' when nothing is found (712), and returns a real
    nested hit."""
    nondir = str(tmp_path / "does_not_exist")
    # non-dir path + a NO_RECURSE system dir -> ''
    assert _lm._find_espeak_lib_recursive([nondir, "/usr/lib"], {"libespeak.so"}) == ""
    # a real nested library is found
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    lib = nested / "libespeak.so"
    lib.write_text("")
    assert _lm._find_espeak_lib_recursive([str(tmp_path)], {"libespeak.so"}) == str(lib)


def test_get_espeak_env_direct_file(tmp_path, monkeypatch):
    """A configured path that IS an espeak library file is returned directly
    (lines 730, 732-733)."""
    monkeypatch.delenv("PATH_ESPEAK", raising=False)
    monkeypatch.delenv("PHONEMIZER_ESPEAK_LIBRARY", raising=False)
    libfile = tmp_path / "libespeak.dylib"
    libfile.write_text("")
    assert get_espeak_env([str(libfile)]) == str(libfile)


def test_get_espeak_env_glob_fallback_and_warning(monkeypatch):
    """With no usable configured path, get_espeak_env falls back to the system
    glob (lines 747-749); if even that fails it warns and returns '' (750-751)."""
    monkeypatch.delenv("PATH_ESPEAK", raising=False)
    monkeypatch.delenv("PHONEMIZER_ESPEAK_LIBRARY", raising=False)
    # on this machine / CI espeak is installed, so the system glob resolves it
    found = _lm._glob_espeak_lib()
    if found:
        assert get_espeak_env([]) == found
    # force the glob to fail -> warning path, returns ''
    monkeypatch.setattr(_lm, "_glob_espeak_lib", lambda *a, **k: "")
    assert get_espeak_env([]) == ""


def test_language_factory_de_generic_and_get_word():
    """Language() dispatches to the German subclass and to a bare LanguageModel
    for an unknown code (lines 775-782); get_word routes through Language().get()."""
    assert type(Language("de")).__name__ == "GermanLanguage"
    generic = Language("zz")
    assert type(generic) is LanguageModel
    assert generic.lang == "zz"
    assert get_word("with", lang="en")[0] == Language("en").get("with")[0]
