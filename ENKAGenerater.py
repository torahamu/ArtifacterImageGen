import math
import psutil
from cachetools import TTLCache
from functools import partial
import requests
from io import BytesIO
from PIL import Image,ImageFont,ImageDraw,ImageEnhance,ImageFilter, ImageFile
import os 
import base64
import time
import asyncio

from enkanetwork import EnkaNetworkAPI
from enkanetwork import EnkaNetworkAPI, EquipmentsType, DigitType
from enkanetwork.model.stats import Stats

ImageFile.LOAD_TRUNCATED_IMAGES = True
client = EnkaNetworkAPI()
cwd = os.path.abspath(os.path.dirname(__file__))
config_font = lambda size : ImageFont.truetype(f'{cwd}/Resources/Assets/ja-jp.ttf',size)
image_dict = {}

elementjp = {
    "Ice":"氷",
    "Electric":"雷",
    "Grass":"草",
    "Rock":"岩",
    "Fire":"炎",
    "Water":"水",
    "Wind":"風",
}

FIGHT_PROPJP = {
    "FIGHT_PROP_FIRE_ADD_HURT":"炎元素ダメージ",
    "FIGHT_PROP_ELEC_ADD_HURT":"雷元素ダメージ",
    "FIGHT_PROP_WATER_ADD_HURT":"水元素ダメージ",
    "FIGHT_PROP_GRASS_ADD_HURT":"草元素ダメージ",
    "FIGHT_PROP_WIND_ADD_HURT":"風元素ダメージ",
    "FIGHT_PROP_ROCK_ADD_HURT":"岩元素ダメージ",
    "FIGHT_PROP_ICE_ADD_HURT":"氷元素ダメージ",
    "FIGHT_PROP_PHYSICAL_ADD_HURT":"物理ダメージ",
    "FIGHT_PROP_HEAL_ADD":"与える治癒効果",
}

image_paths = {
    'ice':                         f'{cwd}/Resources/Base/Ice.png',
    'electric':                    f'{cwd}/Resources/Base/Electric.png',
    'fire':                        f'{cwd}/Resources/Base/fire.png',
    'grass':                       f'{cwd}/Resources/Base/Grass.png',
    'rock':                        f'{cwd}/Resources/Base/Rock.png',
    'water':                       f'{cwd}/Resources/Base/Water.png',
    'wind':                        f'{cwd}/Resources/Base/Wind.png',
    'constellation_ice':           f'{cwd}/Resources/命の星座/Ice.png',
    'constellation_electric':      f'{cwd}/Resources/命の星座/Electric.png',
    'constellation_fire':          f'{cwd}/Resources/命の星座/Fire.png',
    'constellation_grass':         f'{cwd}/Resources/命の星座/Grass.png',
    'constellation_rock':          f'{cwd}/Resources/命の星座/Rock.png',
    'constellation_water':         f'{cwd}/Resources/命の星座/Water.png',
    'constellation_wind':          f'{cwd}/Resources/命の星座/Wind.png',
    'constellation_ice_LOCK':      f'{cwd}/Resources/命の星座/IceLOCK.png',
    'constellation_electric_LOCK': f'{cwd}/Resources/命の星座/ElectricLOCK.png',
    'constellation_fire_LOCK':     f'{cwd}/Resources/命の星座/FireLOCK.png',
    'constellation_grass_LOCK':    f'{cwd}/Resources/命の星座/GrassLOCK.png',
    'constellation_rock_LOCK':     f'{cwd}/Resources/命の星座/RockLOCK.png',
    'constellation_water_LOCK':    f'{cwd}/Resources/命の星座/WaterLOCK.png',
    'constellation_wind_LOCK':     f'{cwd}/Resources/命の星座/WindLOCK.png',
    'TalentBack':                  f'{cwd}/Resources/Assets/TalentBack.png',
    'Alhaitham':                   f'{cwd}/Resources/Assets/Alhaitham.png',
    'ArtifactMask':                f'{cwd}/Resources/Assets/ArtifactMask.png',
    'CharacterMask':               f'{cwd}/Resources/Assets/CharacterMask.png',
    'Love':                        f'{cwd}/Resources/Assets/Love.png',
    'Shadow':                      f'{cwd}/Resources/Assets/Shadow.png',
    'Rare1':                       f'{cwd}/Resources/Assets/Rarelity/1.png',
    'Rare2':                       f'{cwd}/Resources/Assets/Rarelity/2.png',
    'Rare3':                       f'{cwd}/Resources/Assets/Rarelity/3.png',
    'Rare4':                       f'{cwd}/Resources/Assets/Rarelity/4.png',
    'Rare5':                       f'{cwd}/Resources/Assets/Rarelity/5.png',
    'TalentBase':                  f'{cwd}/Resources/Assets/TalentBack.png',
    'PMask':                       f'{cwd}/Resources/Assets/ArtifactMask.png',
    'BaseAtk':                     f'{cwd}/Resources/emotes/基礎攻撃力.png',
    'score_A' :                    f'{cwd}/Resources/artifactGrades/A.png',
    'score_B' :                    f'{cwd}/Resources/artifactGrades/B.png',
    'score_S' :                    f'{cwd}/Resources/artifactGrades/S.png',
    'score_SS':                    f'{cwd}/Resources/artifactGrades/SS.png',
}

optionmap = {
    "攻撃力パーセンテージ":"攻撃%",
    "防御力パーセンテージ":"防御%",
    "元素チャージ効率":"元チャ効率",
    "HPパーセンテージ":"HP%",
}

PointRefer = {
    "total": {
        "SS": 220,
        "S": 200,
        "A": 180
    },
    "EQUIP_BRACER": {
        "SS": 50,
        "S": 45,
        "A": 40
    },
    "EQUIP_NECKLACE": {
        "SS": 50,
        "S": 45,
        "A": 40
    },
    "EQUIP_SHOES": {
        "SS": 45,
        "S": 40,
        "A": 35
    },
    "EQUIP_RING": {
        "SS": 45,
        "S": 40,
        "A": 37
    },
    "EQUIP_DRESS": {
        "SS": 40,
        "S": 35,
        "A": 30
    }
}

async def download_or_get_existing_file(file_path, url):
    folder = os.path.dirname(file_path)
    if not os.path.exists(folder):
        os.makedirs(folder)
    if not os.path.isfile(file_path):
        response = requests.get(url)
        with open(file_path, "wb") as file:
            file.write(response.content)
    return Image.open(file_path)

async def load_image_async(path):
    return Image.open(path)

async def load_images_async(paths):
    tasks = [asyncio.create_task(load_image_async(path)) for path in paths]
    return await asyncio.gather(*tasks)

async def initialize():
    global image_dict

    images = await load_images_async(image_paths.values())
    image_dict = dict(zip(image_paths.keys(), images))

async def pil_to_base64(img, format="jpeg"):
    buffer = BytesIO()
    img.save(buffer, format)
    img_str = base64.b64encode(buffer.getvalue()).decode("ascii")

    return img_str

async def status_text(character, BaseImage):
    def status_text_sub(i, parameter, D):
        #{stat[1].to_rounded() if isinstance(stat[1], Stats) else stat[1].to_percentage_symbol()}
        val = getattr(character.stats, parameter)
        str = math.floor(val.value) if isinstance(val, Stats) else val.to_percentage_symbol()
        if isinstance(str, (int, float)):
            statelen = D.textlength(format(str,','),config_font(26))
            D.text((1360-statelen,67+i*70),format(str,','),font=config_font(26))
        else:
            statelen = D.textlength(str,config_font(26))
            D.text((1360-statelen,67+i*70),str,font=config_font(26))

    if character.id == 10000054:
        max_prop = 'FIGHT_PROP_HEAL_ADD'
    else:
        prop_dict = {
            "FIGHT_PROP_FIRE_ADD_HURT": character.stats.FIGHT_PROP_FIRE_ADD_HURT.to_percentage(),
            "FIGHT_PROP_ELEC_ADD_HURT": character.stats.FIGHT_PROP_ELEC_ADD_HURT.to_percentage(),
            "FIGHT_PROP_WATER_ADD_HURT": character.stats.FIGHT_PROP_WATER_ADD_HURT.to_percentage(),
            "FIGHT_PROP_GRASS_ADD_HURT": character.stats.FIGHT_PROP_GRASS_ADD_HURT.to_percentage(),
            "FIGHT_PROP_WIND_ADD_HURT": character.stats.FIGHT_PROP_WIND_ADD_HURT.to_percentage(),
            "FIGHT_PROP_ROCK_ADD_HURT": character.stats.FIGHT_PROP_ROCK_ADD_HURT.to_percentage(),
            "FIGHT_PROP_ICE_ADD_HURT": character.stats.FIGHT_PROP_ICE_ADD_HURT.to_percentage(),
            "FIGHT_PROP_PHYSICAL_ADD_HURT": character.stats.FIGHT_PROP_PHYSICAL_ADD_HURT.to_percentage(),
        }
        max_prop = max(prop_dict, key=prop_dict.get)
        if prop_dict[max_prop] == 0:
            #max_prop = f"FIGHT_PROP_{character.element.upper()}_ADD_HURT"
            max_prop = f"FIGHT_PROP_ELEC_ADD_HURT"

    max_prop_text = FIGHT_PROPJP.get(max_prop)

    StatusTextImage = Image.new("RGBA",BaseImage.size,(255,255,255,0))
    D = ImageDraw.Draw(StatusTextImage)
    D.text((844,67+7*70),max_prop_text,font=config_font(26))

    status_text_sub(0, 'FIGHT_PROP_MAX_HP', D)
    status_text_sub(1, 'FIGHT_PROP_CUR_ATTACK', D)
    status_text_sub(2, 'FIGHT_PROP_CUR_DEFENSE', D)
    status_text_sub(3, 'FIGHT_PROP_ELEMENT_MASTERY', D)
    status_text_sub(4, 'FIGHT_PROP_CRITICAL', D)
    status_text_sub(5, 'FIGHT_PROP_CRITICAL_HURT', D)
    status_text_sub(6, 'FIGHT_PROP_CHARGE_EFFICIENCY', D)
    status_text_sub(7, max_prop, D)
    return StatusTextImage

async def status_info(character, BaseImage):
    if character.id == 10000054:
        max_prop = 'FIGHT_PROP_HEAL_ADD'
    else:
        prop_dict = {
            "FIGHT_PROP_FIRE_ADD_HURT": character.stats.FIGHT_PROP_FIRE_ADD_HURT.to_percentage(),
            "FIGHT_PROP_ELEC_ADD_HURT": character.stats.FIGHT_PROP_ELEC_ADD_HURT.to_percentage(),
            "FIGHT_PROP_WATER_ADD_HURT": character.stats.FIGHT_PROP_WATER_ADD_HURT.to_percentage(),
            "FIGHT_PROP_GRASS_ADD_HURT": character.stats.FIGHT_PROP_GRASS_ADD_HURT.to_percentage(),
            "FIGHT_PROP_WIND_ADD_HURT": character.stats.FIGHT_PROP_WIND_ADD_HURT.to_percentage(),
            "FIGHT_PROP_ROCK_ADD_HURT": character.stats.FIGHT_PROP_ROCK_ADD_HURT.to_percentage(),
            "FIGHT_PROP_ICE_ADD_HURT": character.stats.FIGHT_PROP_ICE_ADD_HURT.to_percentage(),
            "FIGHT_PROP_PHYSICAL_ADD_HURT": character.stats.FIGHT_PROP_PHYSICAL_ADD_HURT.to_percentage(),
        }
        #{FIGHT_PROPJP.get(max_prop)}
        max_prop = max(prop_dict, key=prop_dict.get)
        if prop_dict[max_prop] == 0:
            #max_prop = f"FIGHT_PROP_{character.element.upper()}_ADD_HURT"
            max_prop = f"FIGHT_PROP_ELEC_ADD_HURT"

    max_prop_text = FIGHT_PROPJP.get(max_prop)
    opicon = Image.open(f'{cwd}/Resources/emotes/{max_prop_text}.png').resize((40,40))
    opmask = opicon.copy()
    oppaste = Image.new('RGBA',BaseImage.size,(255,255,255,0))
    oppaste.paste(opicon,(789,65+7*70))
    return oppaste

async def character_info(character, BaseImage):
    if character.id == 10000005:
        CharacterImage = Image.open(f'{cwd}/Resources/character/空(風)/avatar.png')
    elif character.id == 10000007:
        CharacterImage = Image.open(f'{cwd}/Resources/character/蛍(風)/avatar.png')
    else:
        response = requests.get(character.image.banner.url)
        CharacterImage = Image.open(BytesIO(response.content))
    CharacterImage = CharacterImage.crop((289,0,1728,1024))
    CharacterImage = CharacterImage.resize((int(CharacterImage.width*0.75), int(CharacterImage.height*0.75)))
    CharacterAvatarMask = CharacterImage.copy()
    if character.name == 'アルハイゼン':
        CharacterAvatarMask2 = image_dict['Alhaitham'].convert('L').resize(CharacterImage.size)
    else:
        CharacterAvatarMask2 = image_dict['CharacterMask'].convert('L').resize(CharacterImage.size)
    CharacterImage.putalpha(CharacterAvatarMask2)
    CharactersAddImage = Image.new("RGBA",BaseImage.size,(255,255,255,0))
    Shadow = image_dict['Shadow'].resize(BaseImage.size)
    CharactersAddImage.paste(CharacterImage,(-160,-45),mask=CharacterAvatarMask)
    CharactersAddImage = Image.alpha_composite(CharactersAddImage,Shadow)

    return CharactersAddImage

async def character_text(character, BaseImage):
    CharactersTextImage = Image.new("RGBA",BaseImage.size,(255,255,255,0))
    D = ImageDraw.Draw(CharactersTextImage)
    D.text((30,20),character.name,font=config_font(48))

    level_text =f"{character.level} / {character.max_level}"
    friend_text = str(character.friendship_level)

    friendshiplength = D.textlength(friend_text,font=config_font(25))
    D.text((35,75),"Lv."+level_text,font=config_font(25))

    D.rounded_rectangle((35,114,77+friendshiplength,142),radius=2,fill="black")
    FriendShipIcon = image_dict['Love'].convert("RGBA")
    FriendShipIcon = FriendShipIcon.resize((int(FriendShipIcon.width*(24/FriendShipIcon.height)),24))
    Fmask = FriendShipIcon.copy()
    CharactersTextImage.paste(FriendShipIcon,(42,116),mask=Fmask)
    D.text((73,114),friend_text,font=config_font(25))

    return CharactersTextImage

async def skill_text(character, BaseImage):
    TalentAddImage = Image.new("RGBA",BaseImage.size,(255,255,255,0))
    D = ImageDraw.Draw(TalentAddImage)

    D.text((42,397),f'Lv.{character.skills[0].level}',font=config_font(17),fill='aqua' if character.skills[0].level >= 10 else None)
    D.text((42,502),f'Lv.{character.skills[1].level}',font=config_font(17),fill='aqua' if character.skills[1].level >= 10 else None)
    D.text((42,607),f'Lv.{character.skills[2].level}',font=config_font(17),fill='aqua' if character.skills[2].level >= 10 else None)

    return TalentAddImage

async def skill_info(character, BaseImage):
    TalentBase = image_dict[f'TalentBase']
    TalentAddImage = Image.new("RGBA",BaseImage.size,(255,255,255,0))
    TalentBase = TalentBase.resize((int(TalentBase.width/1.5),int(TalentBase.height/1.5)))
    
    for i,skill in enumerate(character.skills):
        TalentPaste = Image.new("RGBA",TalentBase.size,(255,255,255,0))
        
        if i == 0:
            skill_name = '通常'
        elif i == 1:
            skill_name = 'スキル'
        elif i == 2:
            skill_name = '爆発'
        else:
            skill_name = '通常'
        TalentImage = await download_or_get_existing_file(f'{cwd}/Resources/character/{character.name}/{skill_name}.png', character.image.banner.url)
        TalentImage = TalentImage.convert("RGBA").resize((50,50)).convert('RGBA')
        TalentMask = TalentImage.copy()
        TalentPaste.paste(TalentImage,(TalentPaste.width//2-25,TalentPaste.height//2-25),mask=TalentMask)
        
        TalentObject = Image.alpha_composite(TalentBase,TalentPaste)
        TalentAddImage.paste(TalentObject,(15,330+i*105))
    return TalentAddImage

async def weapon_text(character, BaseImage):
    weapon = character.equipments[-1]
    WeaponTextImage = Image.new("RGBA",BaseImage.size,(255,255,255,0))
    D = ImageDraw.Draw(WeaponTextImage)
    D.text((1582,47),weapon.detail.name,font=config_font(26))
    wlebellen = D.textlength(f'Lv.{weapon.level}',font=config_font(24))
    D.rounded_rectangle((1582,80,1582+wlebellen+4,108),radius=1,fill='black')
    D.text((1584,82),f'Lv.{weapon.level}',font=config_font(24))
    D.text((1623,120),f'基礎攻撃力  {weapon.detail.mainstats.value}',font=config_font(23))
    
    if len(weapon.detail.substats) > 0:
        substate = weapon.detail.substats[0]
        D.text((1623,155),f"{optionmap.get(substate.name) or substate.name}  {substate.value}{'%' if substate.type == DigitType.PERCENT else ''}",font=config_font(23))
    
    D.rounded_rectangle((1430,45,1470,70),radius=1,fill='black')
    D.text((1433,46),f'R{weapon.refinement}',font=config_font(24))
    return WeaponTextImage

async def weapon_info(character, BaseImage):
    weapon = character.equipments[-1]

    WeaponImage = await download_or_get_existing_file(f'{cwd}/Resources/weapon/{weapon.detail.name}.png', weapon.detail.icon.url)
    WeaponImage = WeaponImage.convert("RGBA").resize((128,128))
    WeaponMask = WeaponImage.copy()
    
    WeaponRImage = image_dict[f'Rare{weapon.detail.rarity}'].convert("RGBA")
    WeaponRImage = WeaponRImage.resize((int(WeaponRImage.width*0.97),int(WeaponRImage.height*0.97)))
    WeaponRMask = WeaponRImage.copy()
    
    BaseAtk = image_dict['BaseAtk']
    BaseAtk = BaseAtk.resize((23,23))
    BaseAtkmask = BaseAtk.copy()

    if len(weapon.detail.substats) > 0:
        SubAtk = Image.open(f'{cwd}/Resources/emotes/{weapon.detail.substats[0].name}.png').resize((23,23))
        SubAtk = SubAtk.resize((23,23))
        SubAtkmask = SubAtk.copy()

    WeaponAddImage = Image.new("RGBA",BaseImage.size,(255,255,255,0))
    WeaponAddImage.paste(WeaponImage,(1430,50),mask=WeaponMask)
    WeaponAddImage.paste(WeaponRImage,(1422,173),mask=WeaponRMask)
    WeaponAddImage.paste(BaseAtk,(1600,120),mask=BaseAtkmask)
    WeaponAddImage.paste(SubAtk,(1600,155),mask=SubAtkmask)

    return WeaponAddImage

async def constellation_info(character, BaseImage):
    CBase = image_dict[f'constellation_{character.element.lower()}'].resize((90,90)).convert('RGBA')
    Clock = image_dict[f'constellation_{character.element.lower()}_LOCK'].resize((90,90)).convert('RGBA')
    ClockMask = Clock.copy()
    
    CAddImage = Image.new("RGBA",BaseImage.size,(255,255,255,0))
    for c in range(1,7):
        if c > character.constellations_unlocked:
            CAddImage.paste(Clock,(666,-10+c*93),mask=ClockMask)
        else:
            CharaC = await download_or_get_existing_file(f'{cwd}/Resources/character/{character.name}/{c}.png', character.constellations[c-1].icon.url)
            CharaC = CharaC.convert("RGBA").resize((45,45))
            CharaCPaste = Image.new("RGBA",CBase.size,(255,255,255,0))
            CharaCMask = CharaC.copy()
            CharaCPaste.paste(CharaC,(int(CharaCPaste.width/2)-25,int(CharaCPaste.height/2)-23),mask=CharaCMask)
            
            Cobject = Image.alpha_composite(CBase,CharaCPaste)
            CAddImage.paste(Cobject,(666,-10+c*93))
    
    return CAddImage

async def score_calc(artifact_value_dict, type):
    score = 0.0
    if type == 'HP':
        score += float(artifact_value_dict['会心率'])*2
        score += float(artifact_value_dict['会心ダメージ'])
        score += float(artifact_value_dict['HPパーセンテージ'])
    elif type == '攻撃':
        score += float(artifact_value_dict['会心率'])*2
        score += float(artifact_value_dict['会心ダメージ'])
        score += float(artifact_value_dict['攻撃力パーセンテージ'])
    elif type == '防御':
        score += float(artifact_value_dict['会心率'])*2
        score += float(artifact_value_dict['会心ダメージ'])
        score += float(artifact_value_dict['防御力パーセンテージ'])
    elif type == '元素チャージ効率':
        score += float(artifact_value_dict['会心率'])*2
        score += float(artifact_value_dict['会心ダメージ'])
        score += float(artifact_value_dict['元素チャージ効率'])
    elif type == '元素熟知':
        score += float(artifact_value_dict['会心率'])*2
        score += float(artifact_value_dict['会心ダメージ'])/2
        score += float(artifact_value_dict['元素熟知'])/2
    return math.floor(score * 10) / 10

async def score_text(character, BaseImage, type):
    ScoreTextImage = Image.new('RGBA',BaseImage.size,(255,255,255,0))
    D = ImageDraw.Draw(ScoreTextImage)

    sumscore = 0.0
    artifact_sumvalue_dict = {k: 0.0 for k in [
        "HP",
        "HPパーセンテージ",
        "攻撃力",
        "攻撃力パーセンテージ",
        "防御力",
        "防御力パーセンテージ",
        "会心率",
        "会心ダメージ",
        "元素チャージ効率",
        "元素熟知",
        ]}
    for i, artifact in enumerate(filter(lambda x: x.type == EquipmentsType.ARTIFACT, character.equipments)):
        artifact_value_dict = {k: 0.0 for k in [
            "HP",
            "HPパーセンテージ",
            "攻撃力",
            "攻撃力パーセンテージ",
            "防御力",
            "防御力パーセンテージ",
            "会心率",
            "会心ダメージ",
            "元素チャージ効率",
            "元素熟知",
            ]}

        for a, substate in enumerate(artifact.detail.substats):

            SubOP = substate.name
            if SubOP in ['HP','攻撃力','防御力'] and substate.type == DigitType.PERCENT:
                SubOP = f"{SubOP}パーセンテージ"
            SubVal = substate.value
            if SubOP not in artifact_value_dict:
                artifact_value_dict[SubOP] = SubVal
                artifact_sumvalue_dict[SubOP] = SubVal
            else:
                artifact_value_dict[SubOP] += SubVal
                artifact_sumvalue_dict[SubOP] += SubVal

        score = await score_calc(artifact_value_dict, type)
        sumscore += score

        ATFScorelen = D.textlength(str(score),config_font(36))
        D.text((380+i*373-ATFScorelen,1016),str(score),font=config_font(36))
        D.text((295+i*373-ATFScorelen,1025),'Score',font=config_font(27),fill=(160,160,160))

        if score >= PointRefer[artifact.detail.artifact_type]['SS']:
            ScoreImage = image_dict[f'score_SS']
        elif score >= PointRefer[artifact.detail.artifact_type]['S']:
            ScoreImage = image_dict[f'score_S']
        elif score >= PointRefer[artifact.detail.artifact_type]['A']:
            ScoreImage = image_dict[f'score_A']
        else:
            ScoreImage = image_dict[f'score_B']

        ScoreImage = ScoreImage.resize((ScoreImage.width//11,ScoreImage.height//11))
        SCMask = ScoreImage.copy()
        
        ScoreTextImage.paste(ScoreImage,(85+373*i,1013),mask=SCMask)

    sumscore = math.floor(sumscore * 10) / 10
    if type == 'HP':
        sumscore_label1 = 'HP%'
        sumscore_text1 = math.floor(artifact_sumvalue_dict['HPパーセンテージ'] * 10) / 10
    elif type == '攻撃':
        sumscore_label1 = '攻撃%'
        sumscore_text1 = math.floor(artifact_sumvalue_dict['攻撃力パーセンテージ'] * 10) / 10
    elif type == '防御':
        sumscore_label1 = '防御%'
        sumscore_text1 = math.floor(artifact_sumvalue_dict['防御力パーセンテージ'] * 10) / 10
    elif type == '元素チャージ効率':
        sumscore_label1 = '元素チャージ効率'
        sumscore_text1 = math.floor(artifact_sumvalue_dict['元素チャージ効率'] * 10) / 10
    elif type == '元素熟知':
        sumscore_label1 = '元素熟知'
        sumscore_text1 = math.floor(artifact_sumvalue_dict['元素熟知'] * 10) / 10
    sumscore_label2 = '会心率'
    sumscore_label3 = '会心ダメージ'
    sumscore_text2 = math.floor(artifact_sumvalue_dict['会心率'] * 10) / 10
    sumscore_text3 = math.floor(artifact_sumvalue_dict['会心ダメージ'] * 10) / 10

    sumscore_labelLen1 = D.textlength(f'{sumscore_label1}',config_font(20))
    D.text((1583-sumscore_labelLen1,400),sumscore_label1,font=config_font(20))
    ScoreLen1 = D.textlength(f'{str(sumscore_text1)}',config_font(20))
    D.text((1650-ScoreLen1,400),str(sumscore_text1),font=config_font(20))

    sumscore_labelLen2 = D.textlength(f'{sumscore_label2}',config_font(20))
    D.text((1583-sumscore_labelLen2,445),sumscore_label2,font=config_font(20))
    ScoreLen2 = D.textlength(f'{str(sumscore_text2)}',config_font(20))
    D.text((1650-ScoreLen2,445),str(sumscore_text2),font=config_font(20))

    sumscore_labelLen3 = D.textlength(f'{sumscore_label3}',config_font(20))
    D.text((1583-sumscore_labelLen3,490),sumscore_label3,font=config_font(20))
    ScoreLen3 = D.textlength(f'{str(sumscore_text3)}',config_font(20))
    D.text((1650-ScoreLen3,490),str(sumscore_text3),font=config_font(20))

    ScoreLen = D.textlength(f'{sumscore}',config_font(64))
    D.text((1772-ScoreLen//2,420),str(sumscore),font=config_font(64))
    blen = D.textlength(f'{type}換算',font=config_font(24))
    D.text((1867-blen,585),f'{type}換算',font=config_font(24))
    
    if sumscore >= PointRefer['total']['SS']:
        ScoreEv = image_dict[f'score_SS']
    elif sumscore >= PointRefer['total']['S']:
        ScoreEv = image_dict[f'score_S']
    elif sumscore >= PointRefer['total']['A']:
        ScoreEv = image_dict[f'score_A']
    else:
        ScoreEv = image_dict[f'score_B']
    
    ScoreEv = ScoreEv.resize((ScoreEv.width//8,ScoreEv.height//8))
    EvMask = ScoreEv.copy()
    
    ScoreTextImage.paste(ScoreEv,(1806,345),mask=EvMask)

    return ScoreTextImage

async def artifact_text(character, BaseImage, type):
    ArtifactTextImage = Image.new('RGBA',BaseImage.size,(255,255,255,0))
    D = ImageDraw.Draw(ArtifactTextImage)

    artifact_count_dict = {}
    for i, artifact in enumerate(filter(lambda x: x.type == EquipmentsType.ARTIFACT, character.equipments)):
        # メインオプション
        main_op_name = artifact.detail.mainstats.name
        if main_op_name in ['HP','攻撃力','防御力'] and artifact.detail.mainstats.type == DigitType.PERCENT:
            main_op_name = f"{main_op_name}パーセンテージ"
        mainoplen = D.textlength(optionmap.get(main_op_name) or main_op_name,font=config_font(29))
        D.text((375+i*373-int(mainoplen),655),optionmap.get(main_op_name) or main_op_name,font=config_font(29))
        MainIcon = Image.open(f'{cwd}/Resources/emotes/{main_op_name}.png').convert("RGBA").resize((35,35))
        MainMask = MainIcon.copy()
        ArtifactTextImage.paste(MainIcon,(340+i*373-int(mainoplen),655),mask=MainMask)
        main_op_val = format(artifact.detail.mainstats.value,",")
        main_op_val = f"{main_op_val}{'%' if artifact.detail.mainstats.type == DigitType.PERCENT else ''}"

        mainvsize = D.textlength(main_op_val,config_font(49))
        D.text((375+i*373-mainvsize,690),main_op_val,font=config_font(49))

        levlen = D.textlength(f'+{artifact.level}',config_font(21))
        D.rounded_rectangle((373+i*373-int(levlen),748,375+i*373,771),fill='black',radius=2)
        D.text((374+i*373-levlen,749),f'+{artifact.level}',font=config_font(21))

        for a, substate in enumerate(artifact.detail.substats):

            fill_default = (255, 255, 255)
            fill_usui = (255, 255, 255, 196)
            fill_strong = (0, 255, 191, 255)
            fill_color = fill_default
            SubOP = substate.name
            if SubOP in ['HP','攻撃力','防御力'] and substate.type == DigitType.PERCENT:
                SubOP = f"{SubOP}パーセンテージ"
            elif SubOP in ['HP','攻撃力','防御力'] and substate.type == DigitType.NUMBER:
                fill_color = fill_usui
            if type == 'HP' and SubOP in ['HPパーセンテージ','会心率','会心ダメージ']:
                fill_color = fill_strong
            elif type == '攻撃' and SubOP in ['攻撃力パーセンテージ','会心率','会心ダメージ']:
                fill_color = fill_strong
            elif type == '防御' and SubOP in ['防御力パーセンテージ','会心率','会心ダメージ']:
                fill_color = fill_strong
            elif type == '元素チャージ効率' and SubOP in ['元素チャージ効率','会心率','会心ダメージ']:
                fill_color = fill_strong
            elif type == '元素熟知' and SubOP in ['元素熟知','会心率','会心ダメージ']:
                fill_color = fill_strong
            SubVal = format(substate.value,",")
            SubVal = f"{SubVal}{'%' if substate.type == DigitType.PERCENT else ''}"
            D.text((79+373*i,811+50*a),optionmap.get(SubOP) or SubOP,font=config_font(25),fill=fill_color)
            #if SubOP in ['HP','攻撃力','防御力']:
            #    D.text((79+373*i,811+50*a),optionmap.get(SubOP) or SubOP,font=config_font(25),fill=(255,255,255,190))
            #else:
            #    D.text((79+373*i,811+50*a),optionmap.get(SubOP) or SubOP,font=config_font(25),fill=(255,255,255))
            SubIcon = Image.open(f'{cwd}/Resources/emotes/{SubOP}.png').resize((30,30))
            SubMask = SubIcon.copy()
            ArtifactTextImage.paste(SubIcon,(44+373*i,811+50*a),mask=SubMask)

            SubSize = D.textlength(SubVal,config_font(25))
            D.text((375+i*373-SubSize,811+50*a),SubVal,font=config_font(25),fill=fill_color)
            #if SubOP in ['防御力','攻撃力','HP']:
            #    D.text((375+i*373-SubSize,811+50*a),SubVal,font=config_font(25),fill=(255,255,255,190))
            #else:
            #    D.text((375+i*373-SubSize,811+50*a),SubVal,font=config_font(25),fill=(255,255,255))
        if artifact.detail.artifact_name_set not in artifact_count_dict:
            artifact_count_dict[artifact.detail.artifact_name_set] = 1
        else:
            artifact_count_dict[artifact.detail.artifact_name_set] += 1

    artifact_count_dict_filtered = {k: v for k, v in artifact_count_dict.items() if v >= 2}
    for i,(n,q) in enumerate(artifact_count_dict_filtered.items()):
        if len(artifact_count_dict_filtered) == 2:
            D.text((1536,243+i*35),n,fill=(0,255,0),font=config_font(23))
            D.rounded_rectangle((1818,243+i*35,1862,266+i*35),1,'black')
            D.text((1835,243+i*35),str(q),font=config_font(19))
        if len(artifact_count_dict_filtered) == 1:
            D.text((1536,263),n,fill=(0,255,0),font=config_font(23))
            D.rounded_rectangle((1818,263,1862,288),1,'black')
            D.text((1831,265),str(q),font=config_font(19))

    return ArtifactTextImage

async def artifact_text_notype(character, BaseImage):
    ArtifactTextImage = Image.new('RGBA',BaseImage.size,(255,255,255,0))
    D = ImageDraw.Draw(ArtifactTextImage)

    artifact_count_dict = {}
    for i, artifact in enumerate(filter(lambda x: x.type == EquipmentsType.ARTIFACT, character.equipments)):
        # メインオプション
        main_op_name = artifact.detail.mainstats.name
        if main_op_name in ['HP','攻撃力','防御力'] and artifact.detail.mainstats.type == DigitType.PERCENT:
            main_op_name = f"{main_op_name}パーセンテージ"
        mainoplen = D.textlength(optionmap.get(main_op_name) or main_op_name,font=config_font(29))
        D.text((375+i*373-int(mainoplen),655),optionmap.get(main_op_name) or main_op_name,font=config_font(29))
        MainIcon = Image.open(f'{cwd}/Resources/emotes/{main_op_name}.png').convert("RGBA").resize((35,35))
        MainMask = MainIcon.copy()
        ArtifactTextImage.paste(MainIcon,(340+i*373-int(mainoplen),655),mask=MainMask)
        main_op_val = format(artifact.detail.mainstats.value,",")
        main_op_val = f"{main_op_val}{'%' if artifact.detail.mainstats.type == DigitType.PERCENT else ''}"

        mainvsize = D.textlength(main_op_val,config_font(49))
        D.text((375+i*373-mainvsize,690),main_op_val,font=config_font(49))

        levlen = D.textlength(f'+{artifact.level}',config_font(21))
        D.rounded_rectangle((373+i*373-int(levlen),748,375+i*373,771),fill='black',radius=2)
        D.text((374+i*373-levlen,749),f'+{artifact.level}',font=config_font(21))

        for a, substate in enumerate(artifact.detail.substats):

            fill_default = (255, 255, 255)
            fill_usui = (255, 255, 255, 196)
            fill_strong = (0, 255, 191, 255)
            fill_color = fill_default
            SubOP = substate.name
            if SubOP in ['HP','攻撃力','防御力'] and substate.type == DigitType.PERCENT:
                SubOP = f"{SubOP}パーセンテージ"
            elif SubOP in ['HP','攻撃力','防御力'] and substate.type == DigitType.NUMBER:
                fill_color = fill_usui
            SubVal = format(substate.value,",")
            SubVal = f"{SubVal}{'%' if substate.type == DigitType.PERCENT else ''}"
            D.text((79+373*i,811+50*a),optionmap.get(SubOP) or SubOP,font=config_font(25),fill=fill_color)
            #if SubOP in ['HP','攻撃力','防御力']:
            #    D.text((79+373*i,811+50*a),optionmap.get(SubOP) or SubOP,font=config_font(25),fill=(255,255,255,190))
            #else:
            #    D.text((79+373*i,811+50*a),optionmap.get(SubOP) or SubOP,font=config_font(25),fill=(255,255,255))
            SubIcon = Image.open(f'{cwd}/Resources/emotes/{SubOP}.png').resize((30,30))
            SubMask = SubIcon.copy()
            ArtifactTextImage.paste(SubIcon,(44+373*i,811+50*a),mask=SubMask)

            SubSize = D.textlength(SubVal,config_font(25))
            D.text((375+i*373-SubSize,811+50*a),SubVal,font=config_font(25),fill=fill_color)
            #if SubOP in ['防御力','攻撃力','HP']:
            #    D.text((375+i*373-SubSize,811+50*a),SubVal,font=config_font(25),fill=(255,255,255,190))
            #else:
            #    D.text((375+i*373-SubSize,811+50*a),SubVal,font=config_font(25),fill=(255,255,255))
        if artifact.detail.artifact_name_set not in artifact_count_dict:
            artifact_count_dict[artifact.detail.artifact_name_set] = 1
        else:
            artifact_count_dict[artifact.detail.artifact_name_set] += 1

    artifact_count_dict_filtered = {k: v for k, v in artifact_count_dict.items() if v >= 2}
    for i,(n,q) in enumerate(artifact_count_dict_filtered.items()):
        if len(artifact_count_dict_filtered) == 2:
            D.text((1536,243+i*35),n,fill=(0,255,0),font=config_font(23))
            D.rounded_rectangle((1818,243+i*35,1862,266+i*35),1,'black')
            D.text((1835,243+i*35),str(q),font=config_font(19))
        if len(artifact_count_dict_filtered) == 1:
            D.text((1536,263),n,fill=(0,255,0),font=config_font(23))
            D.rounded_rectangle((1818,263,1862,288),1,'black')
            D.text((1831,265),str(q),font=config_font(19))

    return ArtifactTextImage

async def artifact_info(character, BaseImage):
    ArtifactAddImage = Image.new('RGBA',BaseImage.size,(255,255,255,0))
    for i, artifact in enumerate(filter(lambda x: x.type == EquipmentsType.ARTIFACT, character.equipments)):
        Preview = await download_or_get_existing_file(f'{cwd}/Resources/Artifact/{artifact.detail.artifact_name_set}/{artifact.detail.artifact_type}.png', artifact.detail.icon.url)
        Preview = Preview.resize((256,256))
        enhancer = ImageEnhance.Brightness(Preview)
        Preview = enhancer.enhance(0.6)
        Preview= Preview.resize((int(Preview.width*1.3),int(Preview.height*1.3)))
        Pmask1 = Preview.copy()
        
        Pmask = image_dict[f'PMask'].convert('L').resize(Preview.size)
        Preview.putalpha(Pmask)
        if artifact.detail.artifact_type in ['EQUIP_BRACER','EQUIP_DRESS']:
            ArtifactAddImage.paste(Preview,(-37+373*i,570),mask=Pmask1)
        elif artifact.detail.artifact_type in ['EQUIP_NECKLACE','EQUIP_RING']:
            ArtifactAddImage.paste(Preview,(-36+373*i,570),mask=Pmask1)
        else:
            ArtifactAddImage.paste(Preview,(-35+373*i,570),mask=Pmask1)

    return ArtifactAddImage

async def save_image(character, BaseImage, type):
    result_image = await score_text(character, BaseImage, type)
    MixImage = BaseImage
    MixImage = Image.alpha_composite(MixImage,result_image)
    MixImage.save(f'{cwd}/Tests/{character.name}_{type}.png')

async def process_item(character, BaseImage, type):
    if character.id == 10000005:
        character.name = f'空({elementjp.get(character.element)})'
    elif character.id == 10000007:
        character.name = f'蛍({elementjp.get(character.element)})'
    print(f'{character.name} {type}:開始')
    start_time = time.time()
    result_images = await asyncio.gather(
        character_info(character, BaseImage),
        weapon_info(character, BaseImage),
        skill_info(character, BaseImage),
        constellation_info(character, BaseImage),
        status_info(character, BaseImage),
        artifact_info(character, BaseImage),
#        artifact_text_notype(character, BaseImage),
        artifact_text(character, BaseImage, type),
        character_text(character, BaseImage),
        weapon_text(character, BaseImage),
        status_text(character, BaseImage),
        skill_text(character, BaseImage),
    )
    MixImage = BaseImage
    for result_image in result_images:
        MixImage = Image.alpha_composite(MixImage,result_image)
#    MixImage.save(f'{cwd}/Tests/{character.name}.png')
    await asyncio.gather(
        save_image(character, MixImage, type)
    )
    end_time = time.time()
    print(f'{character.name} {type}:終了: {end_time - start_time}秒')

    return character.name

async def main(uid):
    async with client:
        await client.set_language("jp")
        data = await client.fetch_user_by_uid(uid)
        tasks = []
        for character in data.characters:
            BaseImage = image_dict[character.element.lower()]
            tasks.append(process_item(character, BaseImage, 'HP'))
            if len(tasks) == 8:
                results = await asyncio.gather(*tasks)
                tasks = []  # タスクリストをリセット
            tasks.append(process_item(character, BaseImage, '攻撃'))
            if len(tasks) == 8:
                results = await asyncio.gather(*tasks)
                tasks = []  # タスクリストをリセット
            tasks.append(process_item(character, BaseImage, '防御'))
            if len(tasks) == 8:
                results = await asyncio.gather(*tasks)
                tasks = []  # タスクリストをリセット
            tasks.append(process_item(character, BaseImage, '元素チャージ効率'))
            if len(tasks) == 8:
                results = await asyncio.gather(*tasks)
                tasks = []  # タスクリストをリセット
            tasks.append(process_item(character, BaseImage, '元素熟知'))
            if len(tasks) == 8:
                results = await asyncio.gather(*tasks)
                tasks = []  # タスクリストをリセット
        if tasks:  # 未処理のタスクが残っている場合
            results = await asyncio.gather(*tasks)
            # 結果を処理する

if __name__ == '__main__':
    uid = 800033284
#    uid = 800886885
    process = psutil.Process()
    memory_usage = process.memory_info().rss / 1024 / 1024

    print("現在のメモリ使用量：{} MB".format(memory_usage))
    start_time = time.time()
    asyncio.run(initialize())
    asyncio.run(main(uid))
    end_time = time.time()
    print("実行時間：", end_time - start_time, "秒")
    process = psutil.Process()
    memory_usage = process.memory_info().rss / 1024 / 1024

    print("現在のメモリ使用量：{} MB".format(memory_usage))
