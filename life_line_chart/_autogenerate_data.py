import names
import os
import datetime
from random import random


def generate_gedcom_file():
    """generate some gedcom file"""
    db = {}
    db['n_individuals'] = 0
    db['max_individuals'] = 8000
    db['n_families'] = 0
    db['yougest'] = None
    gedcom_content = f"""
    0 HEAD
1 SOUR Gramps
2 VERS 3.3.0
2 NAME Gramps
1 DATE {datetime.date.today()}
2 TIME 15:35:24
1 SUBM @SUBM@
1 COPR Copyright (c) 2020 Christian Schulze,,,.
1 GEDC
2 VERS 5.5
1 CHAR UTF-8
1 LANG German
"""

    def generate_individual(db, birth_year, sex=None, last_name=None):
        if not sex:
            sex = 'F' if random() < 0.5 else 'M'
        first_name = names.get_first_name(
            gender='male' if sex == 'M' else 'female')
        if random() < 0.3:
            first_name += ' ' + \
                names.get_first_name(gender='male' if sex == 'M' else 'female')
        if not last_name:
            last_name = names.get_last_name()
        birth_place = 'Paris' if random() < 0.5 else 'Rome'
        death_place = 'Zorge' if random() < 0.5 else 'Bruegge'
        db['n_individuals'] += 1
        individual_id = f'@I{db["n_individuals"]}@'
        death_year = birth_year + 40 + int(random()*20)
        db[individual_id] = {
            'birth': birth_year,
            'death': death_year,
            'sex': sex,
            'last_name': last_name
        }
        birth_date = f'1 JUN {birth_year}'
        death_date = f'1 JUN {death_year}'
        if not db['yougest']:
            db['yougest'] = individual_id
        elif db[db['yougest']]['birth'] < birth_year:
            db['yougest'] = individual_id

        db[individual_id]['string'] = f"""0 {individual_id} INDI
1 NAME {first_name} /{last_name}/
1 SEX {sex}
1 BIRT
2 DATE {birth_date}
2 PLAC {birth_place}
1 DEAT
2 DATE {death_date}
2 PLAC {death_place}
"""
        return individual_id

    def generate_family(db, husband_id, wife_id, children_ids, marriage_year, marriage_place=None):
        if not marriage_place:
            marriage_place = 'London' if random() < 0.5 else 'Tokio'
        db['n_families'] += 1
        marriage_date = f'1 MAY {marriage_year}'
        family_id = f"@F{db['n_families']}@"
        db[family_id] = {'string': f"""0 {family_id} FAM
1 HUSB {husband_id}
1 WIFE {wife_id}
1 MARR
2 DATE {marriage_date}
2 PLAC {marriage_place}
"""}
        for child_id in children_ids:
            db[family_id]['string'] += f"1 CHIL {child_id}\n"
        return family_id

    def find_by_birth_date(db, from_year, to_year, sex, exclude=[]):
        ids = []
        for individual_id, data in db.items():
            if not individual_id.startswith('@I'):
                continue
            if 'famc' in data:
                if data['birth'] > from_year and data['birth'] < to_year:
                    if sex == data['sex']:
                        if individual_id not in exclude:
                            ids.append(individual_id)
        if ids:
            return ids[int(random()*len(ids))]
        return None

    def generate_recursive_family(db, start_year=1000, generations=2, husband_id=None, wife_id=None, siblings=[], max_children=5):
        if not husband_id:
            if random() < 0.2:
                exclude = siblings.copy()
                if wife_id:
                    exclude += [wife_id]
                husband_id = find_by_birth_date(
                    db, start_year, start_year + 10, sex='M', exclude=exclude)
            if not husband_id:
                husband_id = generate_individual(
                    db, start_year + int(random()*5), sex='M')
            else:
                print(f'reused {husband_id}')
        if not wife_id:
            if random() < 10.9:
                exclude = siblings.copy() + [husband_id]
                wife_id = find_by_birth_date(
                    db, start_year, start_year + 10, sex='F', exclude=exclude)
            if not wife_id:
                wife_id = generate_individual(
                    db, start_year + int(random()*5), sex='F')
            else:
                print(f'reused {wife_id}')
        n_children = int((1+random()*(max_children-1)) *
                         (1 - db['n_individuals'] / db['max_individuals']))
        marriage_year = start_year + 20 + int(random()*5)
        children_ids = []
        for i in range(n_children):
            children_ids.append(generate_individual(
                db, birth_year=marriage_year + 1 + int(random()*10), last_name=db[husband_id]['last_name']))
        family_id = generate_family(
            db, husband_id, wife_id, children_ids, marriage_year)
        for i in range(n_children):
            db[children_ids[i]]['string'] += "1 FAMC "+family_id + '\n'
            db[children_ids[i]]['famc'] = family_id
            if generations > 0:
                generate_recursive_family(
                    db,
                    db[children_ids[i]]['birth'],
                    generations - 1,
                    children_ids[i] if db[children_ids[i]
                                          ]['sex'] == 'M' else None,
                    children_ids[i] if db[children_ids[i]
                                          ]['sex'] == 'F' else None,
                    children_ids)
        db[husband_id]['string'] += "1 FAMS "+family_id + '\n'
        db[wife_id]['string'] += "1 FAMS "+family_id + '\n'

    generate_recursive_family(db, generations=8, max_children=4)
    for k, v in db.items():
        if k.startswith('@I'):
            gedcom_content += v['string']
    for k, v in db.items():
        if k.startswith('@F'):
            gedcom_content += v['string']

    gedcom_content += '0 TRLR\n'
    open(os.path.join(os.path.dirname(__file__), '..', 'tests',
                      'autogenerated.ged'), 'w').write(gedcom_content)
# generate_gedcom_file()


def generate_individual_images():
    from PIL import Image, ImageDraw, ImageFont

    def generate_one_image(filename, text, font_size=22, pos=(15, 40), size=(100, 100), color=(160, 160, 160)):
        img = Image.new('RGB', size, color=color)

        d = ImageDraw.Draw(img)
        font = ImageFont.truetype(r'arial.ttf', font_size)
        d.text(pos, text, fill=(0, 0, 0), font=font)

        img.save(filename)

    for i in range(20):
        generate_one_image(
            f'tests/images/individual_I6_image_age_{1+i*4}.png', f'Age {1+i*4}')


generate_individual_images()
