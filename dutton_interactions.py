import pandas as pd
import copy

ORG_NAMES = ['Candida',
                'S. equorum',
                'S. succinus',
                'Brevibacterium',
                'Brachybacterium',
                'Penicillium',
                'Scopulariopsis']

# Define a color for each organism
ORG_COLOR_DICT = {}
colors = ['red', 'green', 'blue', 'orange', 'black', 'purple', 'brown']
count = 0
for org in ORG_NAMES:
    ORG_COLOR_DICT[org] = colors[count]
    count += 1

class Pairwise_Excel_Table():
    def __init__(self, path_to_table, day_list, num_reps = 3, max_col = 5):
        self.path_to_table = path_to_table
        self.day_list = day_list
        self.num_reps = num_reps
        self.max_col = max_col

        self.measurement_dict = None
        self.experiment_list = None

        # Now finish the setup
        self.finish_setup()

    def finish_setup(self):
        self.measurement_dict = self.get_measurement_dict()
        self.experiment_list = self.get_experiment_list()

    def get_measurement_dict(self):
        table1 = pd.read_excel(self.path_to_table)
        num_rows = table1.shape[0]

        table1.index.name = 'Replicates'
        table1 = table1.iloc[:, 0:self.max_col]
        columns_unflattened = [['Name'], self.day_list]

        table1.columns = [item for sublist in columns_unflattened for item in sublist]

        cur_measurement = None
        measurement_dict = {}

        for i in range(num_rows):
            cur_row = table1.iloc[i]
            cur_row_name = str(cur_row.iloc[0])
            in_list = [s in cur_row_name for s in ORG_NAMES]
            if any(in_list) and (cur_row_name != 'nan'):
                if cur_row_name in ORG_NAMES:
                    cur_measurement = cur_row_name
                    measurement_dict[cur_measurement] = {}
                else:
                    # Take this row and the next num_repetitions
                    data = table1.iloc[i:i+self.num_reps]
                    # We don't care about the first columns actually, that is metadata
                    data = data.iloc[:, 1:]
                    # We need to repeat the zeroth day for each or else we get NaN
                    data.iloc[:, 0] = data.iloc[0, 0]

                    measurement_dict[cur_measurement][cur_row_name] = data

        return measurement_dict

    def get_experiment_list(self):
        measurement_dict_copy = copy.deepcopy(self.measurement_dict)

        # To avoid duplicates, we delete stuff as we go from the measurement dict

        experiment_list = []

        for k1 in measurement_dict_copy.keys():
            for k2 in measurement_dict_copy[k1].keys():
                if 'alone' in k2: #Alone signifies that the experiment was done alone
                    organism_name = k1
                    growth_df = measurement_dict_copy[k1][k2]
                    org = Organism(organism_name, growth_df, self.day_list)
                    exp = Experiment([org], self.day_list)
                    experiment_list.append(exp)

                    # Delete the entry
                    del measurement_dict_copy[k1][k2]

                if '-' in k2: #A dash signifies a combined experiment
                    # We go by the section this stuff is in...sometimes the order is reversed
                    current_organism_name = k1
                    growth_df = measurement_dict_copy[k1][k2]
                    current_org = Organism(current_organism_name, growth_df, self.day_list)

                    # Now to define the other organism
                    split = k2.split('-')
                    organismA_name = split[0]
                    organismB_name = split[1]

                    desired_organism_name = None
                    if organismA_name == current_organism_name:
                        desired_organism_name = organismB_name
                    else:
                        desired_organism_name = organismA_name

                    # Grab information on the new organism; it may be annoying.

                    desired_dict = measurement_dict_copy[desired_organism_name]
                    other_organism = None
                    other_organism_key = None
                    for other_key in desired_dict.keys():
                        if (organismA_name in other_key) and (organismB_name in other_key):
                            other_organism_df = measurement_dict_copy[desired_organism_name][other_key]
                            other_organism = Organism(desired_organism_name, other_organism_df, self.day_list)
                            other_organism_key = other_key

                    if other_organism is None:
                        print 'Something bad has happened, could not find pair of organisms to add...'

                    exp = Experiment([current_org, other_organism], self.day_list)
                    experiment_list.append(exp)

                    # Delete the entry. Might be dicey.
                    del measurement_dict_copy[k1][k2]
                    del measurement_dict_copy[desired_organism_name][other_organism_key]
        return experiment_list

    def get_desired_experiment(self, desired_org_list):
        """Gets the experiment with the strings in desired_org_list. Make sure that the input is a list!"""
        for x in self.experiment_list:
            if len(x.org_list) == len(desired_org_list):
                truth_list = []
                experiment_orgtypes = [q.org_type for q in x.org_list]
                for desired_org_type in desired_org_list:
                    is_in_list = desired_org_type in experiment_orgtypes
                    truth_list.append(is_in_list)
                if all(truth_list):
                    return x
        print 'I could not find that experiment!'
        return None


    def get_alone_growth_experiment(self, org_name):
        desired_exp = None
        for x in self.experiment_list:
            if len(x.org_list) == 1 and (x.org_list[0].org_type == org_name):
                desired_exp = x
        return desired_exp

    def get_pairwise_growth_experiment(self, org1_name, org2_name):
        desired_exp = None

        for x in self.experiment_list:
            # TODO There is definitely a way to generalize this. This is ok for now though.
            is_correct_length = len(x.org_list) == 2
            is_org1_correct = [org1_name in cur_org_name for cur_org_name in x.org_list]
            is_org2_correct = [org2_name in cur_org_name for cur_org_name in x.org_list]

            if is_correct_length and is_org1_correct and is_org2_correct:
                desired_exp = x

        return x


class Organism():
    """Organisms should only be defined in experiments."""
    def __init__(self, org_type, growth_array, day_list):
        self.org_type = org_type
        self.growth_array = growth_array
        self.day_list = day_list

    def __repr__(self):
        return self.org_type

class Experiment():
    def __init__(self, org_list, day_list, environment = None):
        self.org_list = org_list
        self.day_list = day_list

    def __repr__(self):
        return str(self.org_list) + ' exp'