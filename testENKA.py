from io import BytesIO
from PIL import Image,ImageFont,ImageDraw,ImageEnhance,ImageFilter, ImageFile
import os 
import base64
import time
import asyncio
from collections import Counter

from enkanetwork import EnkaNetworkAPI, EquipmentsType, DigitType
from enkanetwork.model.stats import Stats

ImageFile.LOAD_TRUNCATED_IMAGES = True
client = EnkaNetworkAPI()
cwd = os.path.abspath(os.path.dirname(__file__))
config_font = lambda size : ImageFont.truetype(f'{cwd}/Resources/Assets/ja-jp.ttf',size)


optionmap = {
    "攻撃パーセンテージ":"攻撃%",
    "防御パーセンテージ":"防御%",
    "元素チャージ効率":"元チャ効率",
    "HPパーセンテージ":"HP%",
}

#    Base.show()

def pil_to_base64(img, format="jpeg"):
    buffer = BytesIO()
    img.save(buffer, format)
    img_str = base64.b64encode(buffer.getvalue()).decode("ascii")

    return img_str

async def player_info(data):
    print("=== Player Info ===")
    print(f"プレイヤー名: {data.player.nickname}")
    print(f"冒険者ランク： {data.player.level}")
    print(f"アイコン: {data.player.avatar.icon.url}")
    print(f"説明: {data.player.signature}")
    print(f"アチーブ数: {data.player.achievement}")
    print(f"螺旋: {data.player.abyss_floor} - {data.player.abyss_room}")
    print(f"Cache timeout: {data.ttl}")

async def characters_preview(data):
    print("=== Characters Preview ===")
    for charactersPreview in data.player.characters_preview:
        print("ID:", charactersPreview.id)
        print("Name:", charactersPreview.name)
        print("Icon:", charactersPreview.icon.url)
        print("Level:", charactersPreview.level)

async def name_card(data):
    print("=== Namecard main ===")
    print(f"ID: {data.player.namecard.id}")
    print(f"Name: {data.player.namecard.name}")
    print(f"Banner URL: {data.player.namecard.banner.url}")
    print(f"Navbar URL: {data.player.namecard.navbar.url}")
    print(f"Icon URL: {data.player.namecard.icon.url}")
    print("\n")
    print("=== List Namecard ===")
    for namecard in data.player.namecards:
        print(f"ID: {namecard.id}")
        print(f"Name: {namecard.name}")
        print(f"Banner URL: {namecard.banner.url}")
        print(f"Navbar URL: {namecard.navbar.url}")
        print(f"Icon URL: {namecard.icon.url}")

async def skill_info(character):
    print(f"=== 天賦 {character.name} ===")
    for skill in character.skills:
        print(f"ID: {skill.id}")
        print(f"Name: {skill.name}")
        print(f"Icon: {skill.icon.url}")
        print(f"Level: {skill.level}")
        print("="*18)

async def stats_info(character):
    print(f"=== Stats of {character.name} ===")
    print(character.stats.BASE_HP)
    for stat in character.stats:
        print(f"- {stat[0]}: {stat[1].to_rounded() if isinstance(stat[1], Stats) else stat[1].to_percentage_symbol()}")
    print("="*18)

async def artifacts_info(character):
    print(f"=== {character.name} 聖遺物 ===")
    for artifact in filter(lambda x: x.type == EquipmentsType.ARTIFACT, character.equipments):
        print(f"ID: {artifact.id}")
        print(f"聖遺物名: {artifact.detail.name}")
        print(f"聖遺物種類: {artifact.detail.artifact_type}")
        print(f"聖遺物セット: {artifact.detail.artifact_name_set}")
        print(f"Icon: {artifact.detail.icon.url}")
        print(f"Level: {artifact.level}")
        print(f"メインOP: {artifact.detail.mainstats.name}：{artifact.detail.mainstats.value}{'%' if artifact.detail.mainstats.type == DigitType.PERCENT else ''}")
        for substate in artifact.detail.substats:
            print(f"サブOP: {substate.name}：{substate.value}{'%' if substate.type == DigitType.PERCENT else ''}")

async def artifacts_test(character):
    print(f"=== {character.name} 聖遺物 ===")
    artifact_count_dict = {}
    for artifact in filter(lambda x: x.type == EquipmentsType.ARTIFACT, character.equipments):
        if artifact.detail.artifact_name_set not in artifact_count_dict:
            artifact_count_dict[artifact.detail.artifact_name_set] = 1
        else:
            artifact_count_dict[artifact.detail.artifact_name_set] += 1
    artifact_count_dict_filtered = {k: v for k, v in artifact_count_dict.items() if v >= 2}
    for i,(n,q) in enumerate(artifact_count_dict_filtered.items()):
        print(f'{i}:{n}:{q}')

    print(len(artifact_count_dict_filtered))

async def constellation_info(character):
    print(f"=== {character.name} 凸詳細 ===")
    for constellation in character.constellations:
        print(f"ID: {constellation.id}")
        print(f"Name: {constellation.name}")
        print(f"Icon: {constellation.icon.url}")
        print(f"Unlocked: {constellation.unlocked}")

async def weapon_info(character):
    print(f"=== Weapon of {character.name} ===")
    weapon = character.equipments[-1]
    print(f"ID: {weapon.id}")
    print(f"Name: {weapon.detail.name}")
    print(f"Icon: {weapon.detail.icon.url}")
    print(f"Level: {weapon.level}")
    print(f"Refinement: R{weapon.refinement}")
    print(f"Ascension: {'⭐'*weapon.ascension}")
    print("--- Main Stats ---")
    print(f"Name: {weapon.detail.mainstats.name}")
    print(f"Value: {weapon.detail.mainstats.value}{'%' if weapon.detail.mainstats.type == DigitType.PERCENT else ''}")
    print("--- Sub Stats ---")
    for substate in weapon.detail.substats:
        print(f"Name: {substate.name}")
        print(f"Value: {substate.value}{'%' if substate.type == DigitType.PERCENT else ''}")


async def characters_info(data):
    print("=== Characters ===")
    for character in data.characters:
        print(f"character: {character}")
        print(f"ID: {character.id}")
        print(f"キャラ名: {character.name}")
        print(f"レベル: {character.level} / {character.max_level}")
        print(f"レア: {character.rarity}")
        print(f"属性: {character.element}")
        print(f"好感度: {character.friendship_level}")
        print(f"突破: {'⭐'*character.ascension}")
        print(f"凸: C{character.constellations_unlocked}")
        print(f"経験値: {character.xp}")
        print(f"アイコン: {character.image.icon.url}")
        print(f"横アイコン: {character.image.side.url}")
        print(f"ガチャ絵: {character.image.banner.url}")
        print(f"カードアイコン: {character.image.card.url}")
        await stats_info(character)
#        await skill_info(character)
#        await weapon_info(character)
#        await artifacts_info(character)
#        await artifacts_test(character)
#        await constellation_info(character)

async def main():
    async with client:
        await client.set_language("jp")
        data = await client.fetch_user_by_uid(800033284)
#        await player_info(data)
#        await characters_preview(data)
        await characters_info(data)
#        await name_card(data)

start_time = time.time()
asyncio.run(main())
end_time = time.time()
print("実行時間：", end_time - start_time, "秒")
