from Text import Text
import numpy as np

# class WeightingAnalysis ================
# ========================================
# This class serves to provide an analysis
# of the importants of various constraints
# in determination of the "correct" parse
#
# Given a set of hand-annotated lines,
# this class analyzes the set of possible
# parses for each line to determine the
# possible interpretations. Then, it
# uses a Maximum Entropy optimization
# algorithm to determine the best weighting
# for each contstraint so as to maximize the
# probability of the hand-selected parse(s)
# while minimizing the probability of the
# non-selected parses.

# Based on algorith and mathematics as
# described here: http://homepages.inf.ed.ac.uk/sgwater/papers/OTvar03.pdf
# and loosely informed by MEGrammarTool from Bruce Hayes
class DataPoint:
    def __init__(self, line, scansion, scansion_str, frequency):
        self.line = line
        self.scansion = scansion
        self.scansion_str = scansion_str
        self.frequency = frequency
        self.violations = None

class DataAggregator:

    def __init__(self, meter, data_path, lang, delimeter="|"):
        # initialize basics
        self.meter = meter
        self.lang = lang
        self.has_selected = False

        self.constraints = None
        self.data = self.__build_data_set__(data_path, delimeter)

    def __build_data_set__(self, data_path, delimeter):
        data = self.__extract_provided_data__(data_path, delimeter)
        full_parses = self.__get__parses__(data)

        #for key in full_parses:
            #points = full_parses[key]
            #for datum in points:
                #print datum.line
                #print datum.scansion
                #print datum.frequency
                #print datum.violations
                #print ""

        return full_parses


    def __extract_provided_data__(self, data_path, delimeter):
        data = {}
        with open(data_path) as f:
            for line in f.readlines():
                line = line.strip()
                split = line.split(delimeter)

                text = split[0]
                frequency = float(split[1])
                scansion = split[2]

                if text not in data:
                    data[text] = []

                datum = DataPoint(text, scansion, None, frequency)
                data[text].append(datum)

        return data

    def __get__parses__(self, data):
        full_parses = {}
        for line in data:
            text = Text(line, lang=self.lang, meter=self.meter.id)
            text.parse()

            parses = text.allParses(include_bounded=False)[0]
            parse_list = []

            for parse in parses:

                meter_str = parse.str_meter()
                scansion_str = parse.posString()

                constraint_violations = parse.constraintScores

                # make sure that all constraints are in
                # a consistent order
                if self.constraints is None:
                    self.constraints = []
                    for constraint in constraint_violations:
                        self.constraints.append(constraint)

                constraint_viol_count = []
                for constraint in self.constraints:
                    constraint_viol_count.append(constraint_violations[constraint])

                frequency = 0.0
                for datum in data[line]:
                    if datum.scansion == meter_str:
                        frequency = datum.frequency
                        matched = True

                data_point = DataPoint(line, meter_str, scansion_str, frequency)
                data_point.violations = constraint_viol_count
                parse_list.append(data_point)



            full_parses[line] = parse_list


        return full_parses

    def convert_to_table(self):
        inputs_to_data = {}
        inputs_to_outputs = {}
        feature_count = None

        for line in self.data:
            if line not in inputs_to_outputs:
                inputs_to_outputs[line] = []
                inputs_to_data[line] = ([], [])

            for datum in self.data[line]:
                viols, freqs = inputs_to_data[line]

                viols.append(datum.violations)
                freqs.append(datum.frequency)

                outputs = inputs_to_outputs[line]
                outputs.append(datum.scansion_str)

        for key in inputs_to_data:
            violations, frequencies = inputs_to_data[key]

            violation_matrix = np.array(violations)
            frequency_vector = np.array(frequencies)

            # Normalize frequencies:
            sum_of_freq = np.sum(frequency_vector)
            if (sum_of_freq == 0.0):
                print "ERROR: total frequency of line \"%s\" is 0.0; this is either a test point or the values were ignored due to invalid scansions" % (key)
            frequency_vector = frequency_vector / sum_of_freq

            feature_count = violation_matrix.shape[1]

            inputs_to_data[key] = (violation_matrix, frequency_vector)

        return inputs_to_data, inputs_to_outputs, feature_count

class MaxEntAnalyzer:

    def __init__(self, data_aggregator):
        self.data, self.outputs, self.feature_count = data_aggregator.convert_to_table()
        self.constraints = data_aggregator.constraints

        # for now, the values of mu and sigma_squared are hard-coded
        # in...need to make a way to provide the actual values at
        # runtime

        muVec = []
        sigmaVec = []
        for constraint in self.constraints:
            muVec.append(contraint.mu)
            sigmaVec.append(contraint.sigma)

        self.mu = np.array(muVec)
        self.sigma = np.array(sigmaVec)
        #self.mu = np.zeros([self.feature_count])
        #self.sigma = np.full([self.feature_count], 10000)

        # Initialize the starting weight vector...right now
        # initializes to all zeros..., maybe could randomize?
        self.weights = np.zeros([self.feature_count])

    def train(self, step = 0.1, epochs = 100000, tolerance=1e-4, only_positive_weights = False):
        self.step = step
        self.tolerance = tolerance
        self.iterations = epochs

        for i in range(epochs):
            gradient = self.calculate_gradient()
            if np.linalg.norm(gradient) < tolerance:
                self.iterations = i + 1
                break

            self.weights += step * gradient

            if only_positive_weights:
                for i in range(self.feature_count):
                    if self.weights[i] > 0:
                        self.weights[i] = 0


    def report(self):
        # First, print out weights

        print "=" * 80
        print "=" * 80
        print "MaxEnt REPORT"
        print "=" * 80
        print "=" * 80

        print ""
        print ""
        print "Hyperparameters"
        print "-" * 80
        print "Step Size: {}".format(self.step)
        print "Number of Epochs: {}".format(self.iterations)
        print "Early Stop Tolerance: {}".format(self.tolerance)

        print ""
        print ""
        print "Constraint Weighting"
        print "-" * 80

        for i in range(len(self.constraint_names)):
            weight = self.weights[i]
            print_weight = 0 if weight == 0 else -weight
            print "Constraint {}: {}".format(self.constraint_names[i], print_weight)

        print ""
        print ""
        print "Interpretation Notes"
        print "-" * 80
        print "\t(1) It is possible that two or more scansions have the same"
        print "\t    violation counts for all constraints. From the algorithm's"
        print "\t    perspective, these scansions are indistinguishable, which"
        print "\t    means that they will necessarily split their probabilities."
        print "\t    Either different or more constraints are required in order to "
        print "\t    distinguish between these constraint-similar scansions"

        print ""
        print ""
        print "Input Analysis"
        print "-" * 80

        # Then, print out probabilities for the inputs
        for line in self.outputs:
            print "Line: \"{}\"".format(line)
            print ""
            outs, freqs = self.data[line]
            scans = self.outputs[line]

            probs = self.calculate_probabilities(outs)

            for i in range(freqs.shape[0]):
                print "\tScansion {}: {}".format(i+1, scans[i])
                print "\tViolations: {}".format(outs[i, :].tolist())
                print "\t\tObserved Frequency: {}%".format(100 * freqs[i])
                print "\t\tPredicted Frequency: {}%".format(100 * probs[i])
                print ""

    def calculate_gradient(self):
        gradient = self.calculate_overfit_penalty_gradient()

        for key in self.data:
            outs, freqs = self.data[key]
            quotient = self.calculate_gradient_quotient_term(outs)
            difference = outs - quotient

            unsummed_gradient = freqs[:, None] * difference
            gradient = np.sum(unsummed_gradient, axis=0)

        return gradient

    def calculate_gradient_quotient_term(self, outs):
        scores = np.matmul(outs, self.weights)
        exp_scores = np.exp(scores)

        denominator = np.sum(exp_scores)
        unsummed_numerator = outs * exp_scores[:, None]
        numerator = np.sum(unsummed_numerator, axis = 0)

        return numerator / denominator

    def calculate_overfit_penalty_gradient(self):
        return (self.weights - self.mu) / self.sigma

    def calculate_objective(self):
        weight_penalty = self.calculate_overfit_penalty()

        total = 0.0
        for key in self.data:
            out, freqs = data[key]

            probs = self.calculate_probabilities(out)
            log_probs = np.log(probs)
            total += np.sum(frequencies * log_probs)

        return total - cost

    def calculate_probabilities(self, out):
        scores = np.matmul(out, self.weights)
        exp_scores = np.exp(scores)
        denominator = np.sum(exp_scores)

        return exp_scores / denominator

    def calculate_overfit_penalty(self):
        numerator = (self.weights - self.mu)**2
        denominator = 2 * self.sigma

        return np.sum(numerator / denominator)
