#!/usr/bin/env python3
# The following code was generated by OpenAI Codex as a personal guide
#
# Implement backpropagation with explanations.

import random
import numpy as np


class NeuralNet:
    """
    A simple fully-connected 3-layer neural network
    """

    def __init__(self, layers):
        """
        layers: a list of the number of nodes in each layer.
        """
        self.num_layers = len(layers)
        self.layers = layers
        self.weights = [np.random.standard_normal(
            (layers[layer], layers[layer + 1])) for layer in range(len(layers) - 1)]
        self.biases = [np.random.standard_normal(
            layers[layer + 1]) for layer in range(len(layers) - 1)]

    def feedforward(self, x):
        """
        x: inputs.
        return: outputs.
        """
        for w, b in zip(self.weights, self.biases):
            x = sigmoid(np.dot(x, w) + b)
        return x

    def backpropagate(self, x, y):
        """
        x: inputs.
        y: labels.
        return: gradients of the cost function with respect to the weights and biases.
        """
        # forward pass
        activation = x
        activations = [x]
        zs = []
        for w, b in zip(self.weights, self.biases):
            z = np.dot(activation, w) + b
            zs.append(z)
            activation = sigmoid(z)
            activations.append(activation)

        # backward pass
        # compute gradients of the cost function with respect to the weights and biases
        dCdw = [np.zeros(w.shape) for w in self.weights]
        dCdb = [np.zeros(b.shape) for b in self.biases]

        dCdz = self.cost_derivative(
            activations[-1], y) * sigmoid_derivative(zs[-1])
        dCdw[-1] = np.dot(activations[-2].transpose(), dCdz)
        dCdb[-1] = np.sum(dCdz, axis=0, keepdims=True)

        for layer in range(2, self.num_layers):
            z = zs[-layer]
            dCdz = np.dot(
                dCdz, self.weights[-layer + 1].transpose()) * sigmoid_derivative(z)
            dCdw[-layer] = np.dot(activations[-layer - 1].transpose(), dCdz)
            dCdb[-layer] = np.sum(dCdz, axis=0, keepdims=True)

        return dCdw, dCdb

    def stochastic_gradient_descent(self, training_data, epochs, mini_batch_size, learning_rate, test_data=None,
                                    monitor_test_cost=False, monitor_test_accuracy=False, monitor_training_cost=False,
                                    monitor_training_accuracy=False):
        """
        training_data: a list of tuples (x, y) representing the training inputs and the desired outputs.
        epochs: the number of epochs to train for.
        mini_batch_size: the size of mini batches to use when sampling.
        learning_rate: the learning rate.
        test_data: if supplied, the network will be evaluated against the test data after each epoch, and partial progress printed out.
        monitor_test_cost: if True, will print a cost of the network evaluated against test_data.
        monitor_test_accuracy: if True, will print an accuracy of the network evaluated against test_data.
        monitor_training_cost: if True, will print a cost of the network evaluated against training_data.
        monitor_training_accuracy: if True, will print an accuracy of the network evaluated against training_data.
        """
        if test_data:
            n_test = len(test_data)
        n = len(training_data)
        for j in range(epochs):
            # shuffle the training data
            random.shuffle(training_data)
            # partition the training data into mini batches
            mini_batches = [training_data[k:k + mini_batch_size]
                            for k in range(0, n, mini_batch_size)]
            # update the network for each mini batch
            for mini_batch in mini_batches:
                self.update_mini_batch(mini_batch, learning_rate)
            # evaluate the network
            if test_data:
                print('Epoch {0}: {1} / {2}'.format(j,
                      self.evaluate(test_data), n_test))
            else:
                print('Epoch {0} complete'.format(j))
            # print the cost of the network evaluated against training_data
            if monitor_training_cost:
                cost = self.total_cost(training_data, lmbda)
                print('Cost on training data: {}'.format(cost))
            # print the accuracy of the network evaluated against training_data
            if monitor_training_accuracy:
                accuracy = self.accuracy(training_data, convert=True)
                print('Accuracy on training data: {} / {}'.format(accuracy, n))
            # print the cost of the network evaluated against test_data
            if monitor_test_cost:
                cost = self.total_cost(test_data, lmbda, convert=True)
                print('Cost on test data: {}'.format(cost))
            # print the accuracy of the network evaluated against test_data
            if monitor_test_accuracy:
                accuracy = self.accuracy(test_data)
                print('Accuracy on test data: {} / {}'.format(accuracy, n_test))

    def update_mini_batch(self, mini_batch, learning_rate):
        """
        mini_batch: a list of tuples (x, y) representing the training inputs and the desired outputs.
        learning_rate: the learning rate.
        return: updated weights and biases.
        """
        # initialize gradients of weights and biases
        nabla_w = [np.zeros(w.shape) for w in self.weights]
        nabla_b = [np.zeros(b.shape) for b in self.biases]
        # update gradients of weights and biases
        for x, y in mini_batch:
            dCdw, dCdb = self.backpropagate(x, y)
            nabla_w = [nw + dnw for nw, dnw in zip(nabla_w, dCdw)]
            nabla_b = [nb + dnb for nb, dnb in zip(nabla_b, dCdb)]
        # update the weights and biases
        self.weights = [w - (learning_rate / len(mini_batch))
                        * dw for w, dw in zip(self.weights, nabla_w)]
        self.biases = [b - (learning_rate / len(mini_batch))
                       * db for b, db in zip(self.biases, nabla_b)]

    def evaluate(self, test_data):
        """
        return: number of test inputs for which the neural network outputs the correct result.
        """
        test_results = [(np.argmax(self.feedforward(x)), y)
                        for (x, y) in test_data]
        return sum(int(x == y) for (x, y) in test_results)

    def cost_derivative(self, output_activations, y):
        """
        output_activations: output activations.
        y: labels.
        return: the vector of partial derivatives of cost function w.r.t. the activations of the output layer.
        """
        return output_activations - y

    def accuracy(self, data, convert=False):
        """
        data: training or test data.
        convert: whether to convert a label vector to a one-hot matrix.
        return: number of inputs of which the neural network outputs the correct result.
        """
        # if convert is true, convert a label vector to a one-hot matrix
        if convert:
            results = [(np.argmax(self.feedforward(x)), np.argmax(y))
                       for (x, y) in data]
        else:
            results = [(np.argmax(self.feedforward(x)), y) for (x, y) in data]
        return sum(int(x == y) for (x, y) in results)

    def total_cost(self, data, lmbda, convert=False):
        """
        data: training or test data.
        lmbda: regularization parameter.
        convert: whether to convert a label vector to a one-hot matrix.
        return: cost function value.
        """
        # if convert is true, convert a label vector to a one-hot matrix
        cost = 0.0
        for x, y in data:
            a = self.feedforward(x)
            if convert:
                y = one_hot_matrix(
                    y.reshape(self.layers[-1], 1), self.layers[-1])
            cost += self.cost.fn(a, y) / len(data)
            cost += 0.5 * (lmbda / len(data)) * \
                sum(np.linalg.norm(w) ** 2 for w in self.weights)
        return cost


def sigmoid(z):
    """
    computes the sigmoid of z.
    """
    return 1.0 / (1.0 + np.exp(-z))


def sigmoid_derivative(z):
    """
    computes the derivative of sigmoid function.
    """
    return sigmoid(z) * (1 - sigmoid(z))


def one_hot_matrix(y, n_classes):
    """
    y: a vector of labels.
    n_classes: the number of classes.
    return: a one-hot matrix of labels.
    """
    return np.eye(n_classes)[y]


if __name__ == '__main__':
    # load MNIST data
    training_data = load_data('mnist_dataset/mnist_train.csv')
    test_data = load_data('mnist_dataset/mnist_test.csv')

    # network architecture
    layers = [784, 30, 10]

    # hyperparameters
    epochs = 10
    mini_batch_size = 10
    learning_rate = 3.0
    lmbda = 5.0

    # train the network
    net = NeuralNet(layers)
    net.stochastic_gradient_descent(training_data, epochs, mini_batch_size, learning_rate, test_data=test_data,
                                    monitor_test_cost=True, monitor_test_accuracy=True, monitor_training_cost=True,
                                    monitor_training_accuracy=True)

    # save the network to a file
    try:
        save_network(net)
    except:
        print('Error saving the network.')
