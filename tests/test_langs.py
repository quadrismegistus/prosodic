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
