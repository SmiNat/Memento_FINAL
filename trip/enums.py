from django.db import models
from django.utils.translation import gettext_lazy as _


class TripChoices(models.TextChoices):
    CAMPING = _("Wyjazd pod namiot"), _("Wyjazd pod namiot")
    TREKKING = _("Wyjazd w góry - trekking"), _("Wyjazd w góry - trekking")
    HIKING = _("Wyjazd w góry - wspinaczka"), _("Wyjazd w góry - wspinaczka")
    CYCLING = _("Wyjazd na rower"), _("Wyjazd na rower")
    FISHING = _("Wyjazd na ryby"), _("Wyjazd na ryby")
    SUNBATHING = _("Wyjazd nad morze"), _("Wyjazd nad morze")
    BUSINESS_TRIP = _("Wyjazd służbowy"), _("Wyjazd służbowy")
    OTHER = _("Inny"), _("Inny")


class BasicChecklist(models.TextChoices):
    ID = _("Dowód osobisty"), _("Dowód osobisty")
    PASSPORT = _("Paszport"), _("Paszport")
    DRIVING_LICENCE = _("Prawo jazdy"), _("Prawo jazdy")
    CREDIT_CARD = _("Karty kredytowe"), _("Karty kredytowe")
    CASH = _("Gotówka"), _("Gotówka")
    CURRENCY = _("Waluta"), _("Waluta")
    TICKETS = _("Bilety"), _("Bilety")
    VIGNETTES = _("Winiety"), _("Winiety")
    INSURANCE = _("Ubezpieczenie"), _("Ubezpieczenie")


class KeysChecklist(models.TextChoices):
    APARTMENT_KEYS = _("Mieszkanie/dom"), _("Mieszkanie/dom")
    CAR_KEYS = _("Samochód"), _("Samochód")
    TRUNK_KEYS = _("Bagażnik"), _("Bagażnik")
    LUGGAGE_KEYS = _("Bagaż"), _("Bagaż")
    BICYCLE_KEYS = _("Rower"), _("Rower")
    OTHER_KEYS = _("Pozostałe"), _("Pozostałe")


class CosmeticsChecklist(models.TextChoices):
    TOOTHBRUSH = _("Szczotka do zębów"), _("Szczotka do zębów")
    ELECTRIC_TOOTHBRUSH = _("Szczotka elektryczna"), _("Szczotka elektryczna")
    TOOTHBRUSH_CHARGER = _("Ładowarka do szczoteczki"), _("Ładowarka do szczoteczki")
    TOOTHPASTE = _("Pasta do zębów"), _("Pasta do zębów")
    MOUTHWASH = _("Płyn do płukania"), _("Płyn do płukania")
    DENTAL_FLOSS = _("Nić dentystyczna"), _("Nić dentystyczna")
    SHAMPOO = _("Szampon"), _("Szampon")
    CONDITIONER = _("Odżywka"), _("Odżywka")
    SHOWERGEL = _("Mydło/żel"), _("Mydło/żel")
    SPONGE = _("Gąbka"), _("Gąbka")
    RAZOR = _("Maszynka do golenia"), _("Maszynka do golenia")
    FACE_CREAM = _("Krem do twarzy"), _("Krem do twarzy")
    BODY_LOTION = _("Balsam do ciała"), _("Balsam do ciała")
    SUNSCREEN_CREAM = _("Krem do opalania"), _("Krem do opalania")
    HANDKERCHIEFS = _("Chusteczki higieniczne"), _("Chusteczki higieniczne")
    BABY_WIPES = _("Chusteczki nawilżane"), _("Chusteczki nawilżane")
    TAMPONS = _("Podpaski/tampony"), _("Podpaski/tampony")
    INTIMATE_HYGIENE_PRODUCTS = _("Środki higieny intymnej"), _("Środki higieny intymnej")
    TOILET_PAPER = _("Papier toaletowy"), _("Papier toaletowy")
    COTTON_BUDS = _("Patyczki kosmetyczne"), _("Patyczki kosmetyczne")
    COTTON_BALLS = _("Waciki"), _("Waciki")
    TOWEL = _("Ręcznik"), _("Ręcznik")
    FLIP_FLOPS = _("Klapki"), _("Klapki")
    SCISSORS = _("Nożyczki/pęseta/cążki"), _("Nożyczki/pęseta/cążki")
    MAKEUP = _("Makijaż"), _("Makijaż")
    DEODORANT = _("Dezodorant"), _("Dezodorant")
    RUBBER = _("Gumki"), _("Gumki")


class ElectronicsChecklist(models.TextChoices):
    CELLPHONE = _("Telefon"), _("Telefon")
    CAMERA = _("Aparat fotograficzny"), _("Aparat fotograficzny")
    ELECTRONIC_CABLES = _("Kable"), _("Kable")
    CHARGER = _("Ładowarka"), _("Ładowarka")
    ADAPTER = _("Przejściówka"), _("Przejściówka")
    POWER_BANK = _("Powerbank"), _("Powerbank")
    EARPHONES = _("Słuchawki"), _("Słuchawki")
    NOTEBOOK = _("Laptop"), _("Laptop")
    MOUSE = _("Mysz"), _("Mysz")
    MOUSEPAD = _("Podkładka pod mysz"), _("Podkładka pod mysz")
    LAPTOP_PAD = _("Podkładka pod laptop"), _("Podkładka pod laptop")
    BATTERIES = _("Baterie"), _("Baterie")


class UsefulStaffChecklist(models.TextChoices):
    PAJAMAS = _("Piżama"), _("Piżama")
    INSECT_REPELLENTS = _("Raid"), _("Raid")
    FIRST_AID_KIT = _("Apteczka"), _("Apteczka")
    UMBRELLA = _("Parasol"), _("Parasol")


class TrekkingChecklist(models.TextChoices):
    TREKKING_SHOES = _("Buty trekkingowe"), _("Buty trekkingowe")
    MAPS = _("Mapy"), _("Mapy")
    BACKPACK = _("Plecak trekkingowy"), _("Plecak trekkingowy")
    HEATERS = _("Ogrzewacze"), _("Ogrzewacze")
    TOURIST_SEAT = _("Siedzisko"), _("Siedzisko")
    GOGGLES = _("Okulary/google"), _("Okulary/google")
    HEADLAMP = _("Czołówka"), _("Czołówka")
    BATTERIES = _("Baterie"), _("Baterie")
    HELMET = _("Kask"), _("Kask")
    CLIMBING_IRONS = _("Raki/raczki"), _("Raki/raczki")
    ICE_HAMMER = _("Czekan"), _("Czekan")
    SNOWSHOES = _("Rakiety"), _("Rakiety")
    GAITERS = _("Stuptuty"), _("Stuptuty")
    THERMAL_BLANKET = _("Koc termiczny"), _("Koc termiczny")
    FIRST_AID_KIT = _("Apteczka"), _("Apteczka")
    KNIFE = _("Scyzoryk"), _("Scyzoryk")
    TREKKING_POLES = _("Kijki"), _("Kijki")
    THERMOS = _("Termos"), _("Termos")
    IMPREGNATES = _("Impregnaty"), _("Impregnaty")
    WATERPROOF_PANTS = _("Spodnie przeciwdeszczowe"), _("Spodnie przeciwdeszczowe")
    WATERPROOF_JACKET = _("Kurtka przeciwdeszczowa"), _("Kurtka przeciwdeszczowa")
    RAIN_COVER = _("Pokrowiec na plecak"), _("Pokrowiec na plecak")
    TOOLS = _("Narzędzia"), _("Narzędzia")


class HikingChecklist(models.TextChoices):
    HARNESS = _("Uprząż"), _("Uprząż")
    ROPES = _("Liny"), _("Liny")
    BELAY_DEVICES = _("Przyrządy asekuracyjne"), _("Przyrządy asekuracyjne")
    CARABINERS = _("Karabinki"), _("Karabinki")
    QUICKDRAWS = _("Ekspresy"), _("Ekspresy")
    PULLEY = _("Bloczki"), _("Bloczki")
    STOPPER_SET = _("Kości"), _("Kości")
    PITONS = _("Haki"), _("Haki")
    SCREWS = _("Śruby"), _("Śruby")
    MAGNESIA = _("Magnezja"), _("Magnezja")
    LANYARD = _("Lonża"), _("Lonża")
    AXE = _("Czekan"), _("Czekan")
    CHALK_BAG = _("Worek na magnezję"), _("Worek na magnezję")
    CLIMBING_HOLDS = _("Chwyty"), _("Chwyty")
    HELMET = _("Kask"), _("Kask")
    GLOVES = _("Rękawiczki"), _("Rękawiczki")
    CLIMBING_SHOES = _("Buty do wspinaczki"), _("Buty do wspinaczki")
    CRAMPONS = _("Raki"), _("Raki")


class CyclingChecklist(models.TextChoices):
    SHOES = _("Buty rowerowe"), _("Buty rowerowe")
    GLOVES = _("Rękawiczki rowerowe"), _("Rękawiczki rowerowe")
    JACKET = _("Kurtka/bezrękawnik"), _("Kurtka/bezrękawnik")
    GLASSES = _("Okulary/google"), _("Okulary/google")
    HELMET = _("Kask"), _("Kask")
    CAP = _("Czapka"), _("Czapka")
    HEADBAND = _("Opaska"), _("Opaska")
    CYCLING_SHORTS = _("Spodenki rowerowe"), _("Spodenki rowerowe")
    BIKE = _("Rower"), _("Rower :)")
    WATER_BOTTLE = _("Bidon"), _("Bidon")
    LIGHTNING = _("Oświetlenie"), _("Oświetlenie")
    BICYCLE_COUNTER = _("Licznik"), _("Licznik")
    BICYCLE_CARRIER = _("Bagażnik/sakwy"), _("Bagażnik/sakwy")
    PUMP = _("Pompka"), _("Pompka")
    SEAT_COVER = _("Osłona siedzenia"), _("Osłona siedzenia")
    TOOLS = _("Narzędzia"), _("Narzędzia")
    TUBE = _("Zapasowa dętka"), _("Zapasowa dętka")
    LOCK = _("Zapięcie rowerowe"), _("Zapięcie rowerowe")
    FENDER = _("Błotnik"), _("Błotnik")


class CampingChecklist(models.TextChoices):
    ROOF_RACK = _("Bagażnik dachowy"), _("Bagażnik dachowy")
    TENT = _("Namiot"), _("Namiot")
    PILLOW = _("Poduszka"), _("Poduszka")
    SLEEPING_BAG = _("Śpiwór"), _("Śpiwór")
    FOAM_PAD = _("Karimata"), _("Karimata")
    SLEEPING_BAG_INSERT = _("Wkładka"), _("Wkładka")
    MATTRESS = _("Materac"), _("Materac")
    MATTRESS_PUMP = _("Pompka do materaca"), _("Pompka do materaca")
    MOSQUITO_REPELLENT = _("Środek przeciw komarom"), _("Środek przeciw komarom")
    SPORK = _("Spork"), _("Spork")
    TOURIST_STOVE = _("Kuchenka"), _("Kuchenka")
    GAS = _("Gaz"), _("Gaz")
    MUG = _("Kubek"), _("Kubek")
    FREEZE_DRIED_FOOD = _("Liofilizat"), _("Liofilizat")
    TEA = _("Herbata"), _("Herbata")
    TOURIST_CHAIRS = _("Krzesła"), _("Krzesła")
    TOURIST_TABLE = _("Stół"), _("Stół")
    FLASHLIGHT = _("Latarka"), _("Latarka")
    HEADLAMP = _("Czołówka"), _("Czołówka")


class FishingChecklist(models.TextChoices):
    FISHING_ROD = _("Wędka"), _("Wędka")
    REEL = _("Kołowrotek"), _("Kołowrotek")
    ACCESSORIES = _("Akcesoria do wędki"), _("Akcesoria do wędki")
    SOFT_BAITS = _("Przynęty"), _("Przynęty")
    LURES = _("Zanęty"), _("Zanęty")
    LANDING_NET = _("Podbierak"), _("Podbierak")
    ROD_REST = _("Podpórka"), _("Podpórka")
    WATERPROOF_BAG = _("Wiadro"), _("Wiadro")
    SCALES_MEASURES = _("Waga"), _("Waga")
    KNIFE = _("Nóż"), _("Nóż")


class SunbathingChecklist(models.TextChoices):
    SUNGLASSES = _("Okulary przeciwsłoneczne"), _("Okulary przeciwsłoneczne")
    SUNSCREEN_CREAM = _("Krem do opalania"), _("Krem do opalania")
    BEACH_TOWEL = _("Ręcznik plażowy"), _("Ręcznik plażowy")
    FLIP_FLOPS = _("Klapki"), _("Klapki")
    HEADGEAR = _("Nakrycie głowy"), _("Nakrycie głowy")
    BEACH_SUPPLIES = _("Przybory plażowe"), _("Przybory plażowe")
    SWIMSUIT = _("Strój kąpielowy"), _("Strój kąpielowy")


class BusinessChecklist(models.TextChoices):
    PAPERS = _("Dokumenty"), _("Dokumenty")
    BADGE = _("Karty dostępu"), _("Karty dostępu")
    SUIT = _("Ubiór służbowy / wieczorowy)"), _("Ubiór służbowy / wieczorowy)")


class CostGroup(models.TextChoices):
    TICKETS = _("Bilety"), _("Bilety")
    FUEL = _("Paliwo"), _("Paliwo")
    CAR_RENT = _("Wynajem samochodu"), _("Wynajem samochodu")
    INSURANCE = _("Ubezpieczenie"), _("Ubezpieczenie")
    ACCOMMODATION = _("Noclegi"), _("Noclegi")
    FOOD = _("Wyżywienie"), _("Wyżywienie")
    SOUVENIR = _("Pamiątki"), _("Pamiątki")
    ENTERTAINMENT = _("Rozrywka"), _("Rozrywka")
    MEDICINES = _("Leki"), _("Leki")
    OTHER = _("Inne"), _("Inne")
