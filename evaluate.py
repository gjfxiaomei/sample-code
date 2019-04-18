import engine
import json
import pandas as pd
import numpy as np
from sim_setting import sim_setting_control
import argparse
from utility import parse_arguments

traffic_map = {
        "hangzhou_1x1_bc-tyc_18041607_1848_1h": 221.03,
        "hangzhou_1x1_bc-tyc_18041608_2231_1h": 334.72,
        "hangzhou_1x1_bc-tyc_18041610_2021_1h": 213.20,
        "hangzhou_1x1_kn-hz_18041607_827_1h": 	72.48 ,
        "hangzhou_1x1_kn-hz_18041608_743_1h": 	64.10 ,
        "hangzhou_1x1_qc-yn_18041607_1289_1h": 	117.24,
        "hangzhou_1x1_qc-yn_18041608_1417_1h": 	131.99,
        "hangzhou_1x1_sb-sx_18041607_1671_1h": 	173.85,
        "hangzhou_1x1_sb-sx_18041608_2032_1h": 	290.00,
        "hangzhou_1x1_tms-xy_18041607_1969_1h": 214.77,
        "hangzhou_1x1_tms-xy_18041608_2159_1h": 325.32,

        "syn_1x1_uniform_800_1h":  61.44 ,
        "syn_1x1_uniform_1600_1h": 133.40,
        "syn_1x1_uniform_2400_1h": 189.11,
}

def main():
    args = parse_arguments()
    sim_setting = sim_setting_control
    sim_setting["num_step"] = args.num_step
    evaluate_one_traffic(sim_setting, args.scenario)


def evaluate_one_traffic(dic_sim_setting, scenario):
    roadnetFile = "data/{}/roadnet.json".format(scenario)
    flowFile = "data/{}/flow.json".format(scenario)
    planFile = "data/{}/signal_plan_template.txt".format(scenario)
    outFile = "data/{}/evaluation.txt".format(scenario)

    if check(planFile, dic_sim_setting["num_step"]):
        tt = cal_travel_time(dic_sim_setting, roadnetFile, flowFile, planFile)
        print("====================== travel time ======================")
        print("scenario_{0}: {1:.2f} s".format(scenario, tt))
        print("====================== travel time ======================\n")
        b = baseline_tt[scenario]
        score = (b - tt)/b
        print("====================== score ======================")
        print("scenario_{0}: {1}".format(scenario, score))
        print("====================== score ======================")
        with open(outFile, "w") as f:
            f.write(str(score))
    else:
        print("planFile is invalid, Rejected!")



def cal_travel_time(dic_sim_setting, roadnetFile, flowFile, planFile):
    eng = engine.Engine(dic_sim_setting["interval"], dic_sim_setting["threadNum"],
                        dic_sim_setting["saveReplay"], dic_sim_setting["rlTrafficLight"],
                        dic_sim_setting["changeLane"])
    eng.load_roadnet(roadnetFile)
    eng.load_flow(flowFile)

    plan = pd.read_csv(planFile, sep="\t", header=0, dtype=int)
    intersection_id = plan.columns[0]

    for step in range(dic_sim_setting["num_step"]):
        phase = int(plan.loc[step])
        eng.set_tl_phase(intersection_id, phase)
        eng.next_step()
        current_time = eng.get_current_time()

        if current_time % 100 == 0:
            print("Time: {} / {}".format(current_time, dic_sim_setting["num_step"]))

    return eng.get_score()


def check(planFile, num_step):
    flag = True
    error_info = ''
    try:
        plan = pd.read_csv(planFile, sep='\t', header=0, dtype=int)
    except:
        flag = False
        error_info = 'The format of signal plan is not valid and cannot be read by pd.read_csv!'
        print(error_info)
        return flag

    intersection_id = plan.columns[0]
    if intersection_id != 'intersection_1_1':
        flag = False
        error_info = 'The header intersection_id is wrong (for example: intersection_1_1)!'
        print(error_info)
        return flag

    phases = plan.values
    current_phase = phases[0][0]

    if len(phases) < num_step:
        flag = False
        error_info = 'The time of signal plan is less than the default time!'
        print(error_info)
        return flag

    if current_phase == 0:
        yellow_time = 1
    else:
        yellow_time = 0

    # get first green phase and check
    last_green_phase = '*'
    for next_phase in phases[1:]:
        next_phase = next_phase[0]

        # check phase itself
        if next_phase == '':
            continue
        if next_phase not in [0, 1, 2, 3, 4, 5, 6, 7, 8]:
            flag = False
            error_info = 'Phase must be in [0, 1, 2, 3, 4, 5, 6, 7, 8]!'
            break

        # check changing phase
        if next_phase != current_phase and next_phase != 0 and current_phase != 0:
            flag = False
            error_info = '5 seconds of yellow time must be inserted between two different phase!'
            break

        # check unchangeable phase
        if next_phase != 0 and next_phase == last_green_phase:
            flag = False
            error_info = 'No yellow light is allowed between the same phase!'
            break

        # check yellow time
        if next_phase != 0 and yellow_time != 0 and yellow_time != 5:
            flag = False
            error_info = 'Yellow time must be 5 seconds!'
            break

        # normal
        if next_phase == 0:
            yellow_time += 1
            if current_phase != 0:
                last_green_phase = current_phase
        else:
            yellow_time = 0
        current_phase = next_phase

    if not flag:
        print(error_info)
    return flag


if __name__ == "__main__":
    main()
