use nalgebra::{DMatrix, DVector};
use rand::Rng;
use std::f32::consts::E;
use std::iter;
use std::ops::Range;

type Float = f32;
type Matrix = DMatrix<Float>;
type Vector = DVector<Float>;

const INITIAL_VALUE_OFFSET: Float = 1.0;
const INITIAL_VALUE_RANGE: Range<Float> = 0.0 - INITIAL_VALUE_OFFSET..1.0 + INITIAL_VALUE_OFFSET;

/// Computes the sigmoid function.
fn sigmoid(n: Float) -> Float {
    1.0 / (1.0 + E.powf(-n))
}

/// Requires that input is already in the form of sigmoid(x)
fn d_sigmoid(sigmoid: Float) -> Float {
    sigmoid * (1.0 - sigmoid)
}

/// Generates a random number in the range `range`
fn generate_number(range: Range<Float>) -> Float {
    rand::thread_rng().gen_range(range)
}

/// Generates a random matrix of size `rows` x `cols`
fn generate_matrix(rows: usize, cols: usize) -> Matrix {
    Matrix::from_fn(rows, cols, |_i, _j| generate_number(INITIAL_VALUE_RANGE))
}

/// Generates a random vector of size `size`
fn generate_vector(size: usize) -> Vector {
    Vector::from_fn(size, |_i, _j| generate_number(INITIAL_VALUE_RANGE))
}

/// Runs the neural network for a single layer
fn activate_layer(last_layer: &Vector, weights: &Matrix, biases: &Vector) -> Vector {
    (weights * last_layer + biases).map(sigmoid)
}

/// Gets the derivative of the cost function with respect to the neuron activations.
/// Cost function is (expected - actual)^2
fn dc_da_for_last_layer(actual: &Vector, expected: &Vector) -> Vector {
    2.0 * (expected - actual)
}

/// Gets the derivative of the cost function with respect to the neuron values.
fn da_dz(neuron_values: &Vector) -> Vector {
    neuron_values.map(d_sigmoid)
}

/// Gets the derivative of the cost function with respect to the neuron values from back to front
fn get_dc_dz(weights: &[Matrix], activations: &[Vector], expected: &Vector) -> Vec<Vector> {
    let layer_count = weights.len() + 1;
    let outputs = activations.last().unwrap();
    let dc_da = dc_da_for_last_layer(outputs, expected);
    let da_dz = da_dz(outputs);
    let dc_dz = dc_da.component_mul(&da_dz);
    (1..layer_count - 1)
        .rev()
        .fold(vec![dc_dz], |mut dc_dzs, layer| {
            let outgoing_weights = &weights[layer];
            let neuron_activations = &activations[layer];
            let next_dc_dz = dc_dzs.last().unwrap();
            let dc_da = Vector::from(
                outgoing_weights
                    .column_iter()
                    .map(|weights| weights.dot(next_dc_dz))
                    .collect::<Vec<Float>>(),
            );
            let da_dz = crate::da_dz(neuron_activations);
            let dc_dz = dc_da.component_mul(&da_dz);
            dc_dzs.push(dc_dz);
            dc_dzs
        })
}

/// Runs the neuron network forward and returns the activations of the last layer
fn get_activations(inputs: &Vector, weights: &[Matrix], biases: &[Vector]) -> Vec<Vector> {
    let non_input_layers = weights.len();
    (0..non_input_layers).fold(vec![inputs.clone()], |mut activations, layer| {
        let activation = activate_layer(&activations[layer], &weights[layer], &biases[layer]);
        activations.push(activation);
        activations
    })
}

/// The gradients for a single layer
struct Gradients {
    /// The gradients for the weights
    weights: Matrix,
    /// The gradients for the biases
    biases: Vector,
}

/// Calculates the gradients for a all layers.
/// dc_dzs is the vector of derivatives of the cost function with respect to the neuron values from back to front.
fn get_gradients_from_dc_dz(dc_dzs: Vec<Vector>, activations: &[Vector]) -> Vec<Gradients> {
    let last_activations = activations.iter().rev().skip(1);
    dc_dzs
        .into_iter()
        .zip(last_activations)
        .map(|(dc_dz, last_activation)| {
            // [Outer product](https://en.wikipedia.org/wiki/Outer_product). Same shape as incoming weights.
            // Think of last_activation as the *from* and dc_dz as the *to* of the weight.
            let weight_gradient = &dc_dz * last_activation.transpose();
            let bias_gradient = dc_dz;
            Gradients {
                weights: weight_gradient,
                biases: bias_gradient,
            }
        })
        .rev()
        .collect()
}

/// Runs backpropagation on the neural network and returns the gradients for each layer
fn backpropagate(weights: &[Matrix], activations: &[Vector], expected: &Vector) -> Vec<Gradients> {
    let dc_dzs = get_dc_dz(weights, activations, expected);
    get_gradients_from_dc_dz(dc_dzs, activations)
}

struct NetworkParameters {
    input_size: usize,
    hidden_size: usize,
    output_size: usize,
    hidden_layer_count: usize,
}

struct LearningParameters {
    learning_rate: Float,
}

fn generate_weights(network_parameters: &NetworkParameters) -> Vec<Matrix> {
    let input_to_hidden_weights = generate_matrix(
        network_parameters.hidden_size,
        network_parameters.input_size,
    );
    let hidden_to_hidden_weights = iter::repeat_with(|| {
        generate_matrix(
            network_parameters.hidden_size,
            network_parameters.hidden_size,
        )
    });
    let hidden_to_output_weights = generate_matrix(
        network_parameters.output_size,
        network_parameters.hidden_size,
    );
    iter::once(input_to_hidden_weights)
        .chain(hidden_to_hidden_weights)
        .take(network_parameters.hidden_layer_count)
        .chain(iter::once(hidden_to_output_weights))
        .collect()
}

fn generate_biases(network_parameters: &NetworkParameters) -> Vec<Vector> {
    let hidden_biases = iter::repeat_with(|| generate_vector(network_parameters.hidden_size));
    let output_biases = generate_vector(network_parameters.output_size);
    hidden_biases
        .take(network_parameters.hidden_layer_count)
        .chain(iter::once(output_biases))
        .collect()
}

fn gradient_descent(
    weights: &mut [Matrix],
    biases: &mut [Vector],
    gradients: &[Gradients],
    learning_parameters: &LearningParameters,
) {
    for ((layer_weights, layer_biases), gradients) in
        weights.iter_mut().zip(biases.iter_mut()).zip(gradients)
    {
        *layer_weights += &gradients.weights * learning_parameters.learning_rate;
        *layer_biases += &gradients.biases * learning_parameters.learning_rate;
    }
}

fn main() {
    let network_parameters = NetworkParameters {
        input_size: 2,
        hidden_size: 10,
        output_size: 5,
        hidden_layer_count: 2,
    };
    let learning_parameters = LearningParameters { learning_rate: 0.3 };
    let mut weights = generate_weights(&network_parameters);
    let mut biases = generate_biases(&network_parameters);
    let inputs = generate_vector(network_parameters.input_size);
    let expected = Vector::from_fn(network_parameters.output_size, |i, _j| {
        i as Float / network_parameters.output_size as Float
    });
    let outputs = iter::repeat_with(|| {
        let activations = get_activations(&inputs, &weights, &biases);
        let gradients = backpropagate(&weights, &activations, &expected);
        gradient_descent(&mut weights, &mut biases, &gradients, &learning_parameters);
        activations.last().unwrap().clone()
    })
    .take(1000)
    .collect::<Vec<_>>();
    println!("First output: {}", outputs.first().unwrap());
    println!("Last output: {}", outputs.last().unwrap());
    println!("Expected output: {}", expected);
}
