import copy
import time
import traceback

from pyscript import document
from pyodide.ffi import create_proxy

type_names = {"atk_rate": "伤害",
              'boss_atk_rate': "BOSS伤害",
              'critical_atk_rate': "暴击伤害",
              'final_atk_rate': "最终伤害",
              'ignore_defense': "无视防御"}


def get_float_value(ele_id):
    return float(document.querySelector(f"#{ele_id}").value) if document.querySelector(f"#{ele_id}").value else 0


def final_damage(atk_rate, boss_atk_rate, critical_atk_rate, final_atk_rate, ignore_defense, boss_defense):
    return (1 + (atk_rate + boss_atk_rate) / 100) * (1 + (critical_atk_rate + 35) / 100) * (1 - ((1 - ignore_defense / 100) * boss_defense / 100)) * (1 + final_atk_rate / 100)


def diff_value(atk_rate, boss_atk_rate, critical_atk_rate, final_atk_rate, ignore_defense, boss_defense, new_damage, value_type):
    critical_final = (1 + (critical_atk_rate + 35) / 100)
    defense_final = (1 - ((1 - ignore_defense / 100) * boss_defense / 100))
    final_final = (1 + final_atk_rate / 100)
    atk_final = (1 + (atk_rate + boss_atk_rate) / 100)
    print(critical_final, defense_final, final_final, atk_final, new_damage)
    if value_type == 'atk_rate':
        return new_damage / critical_final / defense_final / final_final  * 100 - boss_atk_rate - 100
    if value_type == 'boss_atk_rate':
        return new_damage / critical_final / defense_final / final_final * 100 - atk_rate - 100
    if value_type == 'critical_atk_rate':
        return new_damage / atk_final / defense_final / final_final * 100 - 135
    if value_type == 'final_atk_rate':
        return new_damage / atk_final / critical_final / defense_final * 100 - 100
    if value_type == 'ignore_defense':
        new_defense_final = new_damage / atk_final / critical_final / final_final
        print("new_defense_final", new_defense_final)
        return (1 - (1 - new_defense_final) / boss_defense * 100) * 100 if boss_defense != 0 else 0
    raise ValueError(f'not support {value_type}')


def get_add_value(new_value, new_type, old_value, final_is_mul):
    if new_type == 'ignore_defense':
        return 100 - 100*(1 - new_value / 100) / (1-old_value/100) if old_value < 100 else 0
    if new_type == 'final_atk_rate' and final_is_mul:
        return (1 + new_value / 100)  / (1 + old_value /100) * 100 - 100
    return new_value - old_value


def boss_atk_calculation(event):

    print("run python")
    event.preventDefault()
    try:
        atk_rate = get_float_value('atkRate')
        boss_atk_rate = get_float_value('bossAtkRate')
        critical_atk_rate = get_float_value('criticalAtkRate')
        final_atk_rate = get_float_value('finalAtkRate')
        ignore_defense = get_float_value('ignoreDefense')
        boss_defense = get_float_value('bossDefense')
        boss_add_type = document.querySelector("#bossAddType").value[4:]
        final_is_mul = document.querySelector("#final_mul").checked
        base_replace_ignore_defense = get_float_value('baseReplaceIgnoreDefense')
        new_replace_ignore_defense = get_float_value('newReplaceIgnoreDefense')
        kwargs = {'atk_rate': atk_rate,
                  'boss_atk_rate': boss_atk_rate,
                  'critical_atk_rate': critical_atk_rate,
                  'final_atk_rate': final_atk_rate,
                  'ignore_defense': ignore_defense,
                  'boss_defense': boss_defense}
        source_damage = final_damage(**kwargs)
        add_value_variable = 'new_' + boss_add_type
        boss_add_value = get_float_value('bossAddValue')
        print(boss_add_type, boss_add_value, final_is_mul)
        if base_replace_ignore_defense:
            source_ignore_defense = 100 - (100 - ignore_defense) * 100 / (100 - base_replace_ignore_defense)
            new_ignore_defense = 100 - ((100 - source_ignore_defense) * (100 - new_replace_ignore_defense) / 100)
            add_value_variable = 'new_ignore_defense'
            boss_add_type = "ignore_defense"
            print(f"replace ignore defense {base_replace_ignore_defense} to {new_replace_ignore_defense}, result: {new_ignore_defense}")
        elif boss_add_type == 'final_atk_rate' and final_is_mul:
            exec(f"{add_value_variable} = (1 + final_atk_rate/100) * ( 1 + boss_add_value/100) * 100 - 100")
        elif boss_add_type != 'ignore_defense':
            print('run code', f"{add_value_variable} = {boss_add_type} + {boss_add_value}")
            exec(f"{add_value_variable} = {boss_add_type} + {boss_add_value}")
        else:
            new_ignore_defense = 100 - ((100 - ignore_defense) * (100 - boss_add_value) / 100)
        new_kwargs = copy.deepcopy(kwargs)
        print(kwargs)
        new_kwargs[boss_add_type] = eval(add_value_variable)
        print(new_kwargs)
        new_damage = final_damage(**new_kwargs)
        result_html = f"原始的最终伤害值为: {round(source_damage, 2)}, 新的最终伤害值为: {round(new_damage, 2)} </br>"

        for value_type, name in type_names.items():
            new_value = diff_value(atk_rate, boss_atk_rate, critical_atk_rate, final_atk_rate, ignore_defense, boss_defense, new_damage,value_type)
            print("new value ", new_value)
            if value_type == 'ignore_defense' and new_value > 100:
                result_html += f"相当于无视防御的总值超过100% </br>"
            else:
                add_value = get_add_value(new_value, value_type, eval(value_type), final_is_mul)
                result_html += f"相当于{name}增加{round(add_value, 2)} </br>"

        document.querySelector("#result").innerHTML = result_html
    except:
        print(traceback.format_exc())
        document.querySelector("#result").innerHTML = traceback.format_exc()


document.querySelector("#boss_submit").addEventListener("click", create_proxy(boss_atk_calculation))
