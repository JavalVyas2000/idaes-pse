##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018-2019, by the
# software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia
# University Research Corporation, et al. All rights reserved.
#
# Please see the files COPYRIGHT.txt and LICENSE.txt for full copyright and
# license information, respectively. Both files are also available online
# at the URL "https://github.com/IDAES/idaes-pse".
##############################################################################
import sys
import os
import io
sys.path.append(os.path.abspath('..')) # current folder is ~/tests


from idaes.surrogate.pysmo.kriging import KrigingModel, ResultReport, MyBounds
import numpy as np
import pandas as pd
import pyutilib.th as unittest
from unittest.mock import patch
from scipy.spatial import distance
import scipy.optimize as opt
import scipy.stats as stats
# from sklearn.metrics import mean_squared_error
import pytest

'''
coverage run test_kriging.py
coverage report -m
coverage html

'''

class KrigingModelTestCases(unittest.TestCase):
    '''
    test__init__01: Check that all default values are correctly loaded when input is sparse with both input arrays are numpy
    test__init__02: Check that all default values are correctly loaded when input is sparse with both input arrays are pandas
    test__init__03: Test behaviour raise ValueError if input is not numpy nor pandas
    test__init__04: Test behaviour raise Exception if numerical_gradients not boolean
    test__init__05: Test behaviour raise Exception if regularization not boolean

    test_covariance_matrix_generator: Test behaviour of covariance_matrix_generator
    
    test_covariance_inverse_generator_01: Test behaviour of covariance_inverse_generator
    test_covariance_inverse_generator_02: Test behaviour of covariance_inverse_generator when np.linalg.LinAlgError = LAE
    
    test_kriging_mean: Test behaviour of kriging_mean
    
    test_y_mu_calculation: Test behaviour of y_mu_calculation
    
    test_kriging_sd: Test behaviour of kriging_sd
    
    test_print_fun: Test behaviour of print_fun
    
    test_objective_function: Test behaviour of objective_function
    
    test_numerical_gradient_01: Test behaviour of numerical_gradient with regularization=True
    test_numerical_gradient_02: Test behaviour of numerical_gradient with regularization=False
    
    test_parameter_optimization_01:  Test behaviour of parameter_optimization with numerical_gradients=True, check length of results = 9, length of results.x = 3, length of results.success =True
    test_parameter_optimization_02:  Test behaviour of parameter_optimization with numerical_gradients=False, check length of results = 7, length of results.x = 3, length of results.minimization_failures =False
    
    test_optimal_parameter_evaluation: Test behaviour of optimal_parameter_evaluation
        all functions in this funtion already covered: covariance_matrix_generator, covariance_inverse_generator, kriging_mean, y_mu_calculation, kriging_sd
    
    test_error_calculation: Test behaviour of error_calculation, checking with sklearn.metrics.mean_squared_error
    
    test_r2_calculation:  Test behaviour of test_r2_calculation

    test_kriging_predict_output_01: Test behavior of kriging_predict_output, check the output dimension
    test_kriging_predict_output_02: Test behavior of kriging_predict_output with singe input
    
    test_kriging_training: Test behaviour of kriging_training, 
        all functions in this funtion already covered: optimal_parameter_evaluation, error_calculation, r2_calculation already covered
        ResultReport __init__ is covered here
    
    test_get_feature_vector_01:
    test_get_feature_vector_02:
        Tests: : Unit tests for get_feature_vector. We verify that:
            - 1: The (key, val) dictionary obtained from the generated IndexParam matches the headers of the data when the input is a dataframe
            - 2: The (key, val) dictionary obtained from the generated IndexParam matches is numerically consistent with that of the input array when a numpy array is supplied. 
    
    test_kriging_generate_expression: test only while it is running or not (not compared values)
    ''' 

    def setUp(self):
        # Data generated from the expression (x_1 + 1)^2 + (x_2 + 1) ^ 2 between 0 and 10 for x_1 and x_2
        x1 = np.linspace(1, 10, 21)
        x2 = np.linspace(1, 10, 21)
        y = np.array([ [i,j,((i + 1) ** 2) + ((j + 1) ** 2)] for i in x1 for j in x2])
        self.full_data = pd.DataFrame({'x1': y[:, 0], 'x2': y[:, 1], 'y': y[:, 2]})

        # Theoretical sample data from range for(x_1 + 1)^2 + (x_2 + 1) ^ 2 between 0 and 10 for x_1 and x_2
        x1 = np.linspace(0, 10, 5)
        x2 = np.linspace(0, 10, 5)
        self.training_data = np.array([ [i,j,((i + 1) ** 2) + ((j + 1) ** 2)] for i in x1 for j in x2])

        # Sample data generated from the expression (x_1 + 1)^2 between 0 and 9
        self.test_data_numpy = np.array([[i,(i+1)**2] for i in range(10)])
        self.test_data_pandas = pd.DataFrame([[i,(i+1)**2] for i in range(10)])
        self.test_data_large =  np.array([[i,(i+1)**2] for i in range(200)])
        self.test_data_numpy_1d = np.array([[(i+1)**2] for i in range(10)])
        self.test_data_numpy_3d = np.array([[i,(i+1)**2,(i+2)**2] for i in range(10)]) 

        self.sample_points_numpy = np.array([[i,(i+1)**2] for i in range(8)])
        self.sample_points_large =  np.array([[i,(i+1)**2] for i in range(100)])
        self.sample_points_pandas= pd.DataFrame([[i,(i+1)**2] for i in range(8)])
        self.sample_points_numpy_1d = np.array([[(i+1)**2] for i in range(8)])
        self.sample_points_numpy_3d = np.array([[i,(i+1)**2,(i+2)**2] for i in range(8)])

    
    def test__init__01(self):
        KrigingClass = KrigingModel(self.test_data_numpy)
        assert KrigingClass.num_grads == True
        assert KrigingClass.regularization == True
    
    def test__init__02(self):
        KrigingClass = KrigingModel(self.test_data_pandas)
        assert KrigingClass.num_grads == True
        assert KrigingClass.regularization == True
    
    def test__init__03(self):
        with pytest.raises(ValueError):
            KrigingClass = KrigingModel(list(self.test_data_numpy))
    
    def test__init__04(self):
        with pytest.raises(Exception):
            KrigingClass = KrigingModel(self.test_data_numpy,numerical_gradients=1)
    
    def test__init__05(self):
        with pytest.raises(Exception):
            KrigingClass = KrigingModel(self.test_data_numpy,regularization=1)
    
    
    def test_covariance_matrix_generator(self):
        KrigingClass = KrigingModel(self.training_data[0:3,:],regularization=True)

        p= 2
        theta = np.array([1,2])
        reg_param = 1.00000000e-06
        cov_matrix = KrigingClass.covariance_matrix_generator(KrigingClass.x_data_scaled, theta, reg_param, p)

        cov_matrix_exp = np.array([[1.000001,   0.60653066, 0.13533528],
                                   [0.60653066, 1.000001,   0.60653066],
                                   [0.13533528, 0.60653066, 1.000001  ]])
        np.testing.assert_array_equal(np.round(cov_matrix,7), np.round(cov_matrix_exp,7))
    
    
    def test_covariance_inverse_generator_01(self):
        KrigingClass = KrigingModel(self.training_data[0:3,:],regularization=True)
        cov_matrix = np.array([[1.000001,   0.60653066, 0.13533528],
                                   [0.60653066, 1.000001,   0.60653066],
                                   [0.13533528, 0.60653066, 1.000001  ]])
        cov_matrix_inv_exp = np.array([[ 1.82957788, -1.51792604,  0.67306158],
                                   [-1.51792604,  2.84133453, -1.51792604],
                                   [ 0.67306158, -1.51792604,  1.82957788]])
        
        inverse_x = KrigingClass.covariance_inverse_generator(cov_matrix)
        np.testing.assert_array_equal(np.round(inverse_x,7), np.round(cov_matrix_inv_exp,7))
        
    def test_covariance_inverse_generator_02(self):
        KrigingClass = KrigingModel(self.training_data[0:3,:],regularization=True)
        cov_matrix = np.array([[0, 0, 0],
                               [0, 0, 0],
                               [0, 0, 0]])
        inverse_x = KrigingClass.covariance_inverse_generator(cov_matrix)
        np.testing.assert_array_equal(np.round(inverse_x,7), np.round(cov_matrix,7))

    
    def test_kriging_mean(self):
        KrigingClass = KrigingModel(self.training_data[0:3,:],regularization=True)
        cov_matrix_inv = np.array([[ 1.82957788, -1.51792604,  0.67306158],
                                   [-1.51792604,  2.84133453, -1.51792604],
                                   [ 0.67306158, -1.51792604,  1.82957788]])
        kriging_mean = KrigingClass.kriging_mean(cov_matrix_inv,KrigingClass.y_data)
        kriging_mean_exp =  20.18496
        assert np.round(kriging_mean_exp,5) == np.round(kriging_mean[0][0],5)


    def test_y_mu_calculation(self):
        KrigingClass = KrigingModel(self.training_data[0:3,:],regularization=True)
        kriging_mean =  20.18496                   
        y_mu = KrigingClass.y_mu_calculation(KrigingClass.y_data, kriging_mean)
        y_mu_exp = np.array([[-18.18496],
                             [ -6.93496],
                             [ 16.81504]])
        np.testing.assert_array_equal(np.round(y_mu,5), np.round(y_mu_exp,5))

    
    def test_kriging_sd(self):
        KrigingClass = KrigingModel(self.training_data[0:3,:],regularization=True)
        cov_matrix_inv = np.array([[ 1.82957788, -1.51792604,  0.67306158],
                                   [-1.51792604,  2.84133453, -1.51792604],
                                   [ 0.67306158, -1.51792604,  1.82957788]])               
        y_mu_exp = np.array([[-18.18496],
                             [ -6.93496],
                             [ 16.81504]])
        sigma_sq = KrigingClass.kriging_sd(cov_matrix_inv, y_mu_exp, KrigingClass.y_data.shape[0])
        sigma_sq_exp = 272.84104637
        assert np.round(sigma_sq_exp,5) == np.round(sigma_sq[0][0],5)
    
    
    def test_print_fun(self):
        KrigingClass = KrigingModel(self.training_data[0:3,:],regularization=True)
        capturedOutput = io.StringIO()
        sys.stdout = capturedOutput  
        KrigingClass.print_fun(1, 2, 3.7)
        sys.stdout = sys.__stdout__ 
        assert "at minimum 2.0000 accepted 3\n" == capturedOutput.getvalue() 
    
    
    def test_objective_function(self):
        KrigingClass = KrigingModel(self.training_data[0:3,:],regularization=True)
        p= 2
        var_vector = np.array([1,2,1.00000000e-06])
        conc_log_like = KrigingClass.objective_function(var_vector, KrigingClass.x_data_scaled,  KrigingClass.y_data, p)

        conc_log_like_exp = 8.0408619
        assert np.round(conc_log_like_exp,5) == np.round(conc_log_like,5)

    
    def test_numerical_gradient_01(self):
        KrigingClass = KrigingModel(self.training_data[0:3],regularization=True)
        p= 2
        var_vector = np.array([1,2,1.00000000e-06])
        grad_vec = KrigingClass.numerical_gradient(var_vector, KrigingClass.x_data_scaled,  KrigingClass.y_data, p)
        grad_vec_exp = np.array([0,0,8.8817842e-10])
        np.testing.assert_array_equal(np.round(grad_vec,5), np.round(grad_vec_exp,5))
        
    def test_numerical_gradient_02(self):
        KrigingClass = KrigingModel(self.training_data[0:3],regularization=False)
        p= 2
        var_vector = np.array([1,2,1.00000000e-06])
        grad_vec = KrigingClass.numerical_gradient(var_vector, KrigingClass.x_data_scaled,  KrigingClass.y_data, p)
        grad_vec_exp = np.array([0,0,0])
        np.testing.assert_array_equal(np.round(grad_vec,5), np.round(grad_vec_exp,5))


    def test_parameter_optimization_01(self):
        KrigingClass = KrigingModel(self.training_data[0:3])
        p= 2
        opt_results = KrigingClass.parameter_optimization(p)
        assert len(opt_results) == 9
        assert len(opt_results.x) == 3
        assert opt_results.success == True
    
    def test_parameter_optimization_02(self):
        KrigingClass = KrigingModel(self.training_data[0:3],numerical_gradients=False)
        p= 2
        opt_results = KrigingClass.parameter_optimization(p)
        assert len(opt_results) == 7
        assert len(opt_results.x) == 3
        assert opt_results.minimization_failures == False


    def test_optimal_parameter_evaluation(self):
        KrigingClass = KrigingModel(self.training_data[0:3])
        p= 2
        var_vector = np.array([1,2,1.00000000e-06])
        theta, reg_param, mean, variance, cov_mat, cov_inv, y_mu = KrigingClass.optimal_parameter_evaluation(var_vector, p)
        np.testing.assert_array_equal(theta, [10**1,10**2])
        np.testing.assert_array_equal(reg_param, 1.00000000e-06)
        
    
    def test_error_calculation(self):
        KrigingClass = KrigingModel(self.training_data[0:3],regularization=False)
        p= 2
        var_vector = np.array([1,2,1.00000000e-06])
        theta, reg_param, mean, variance, cov_mat, cov_inv, y_mu = KrigingClass.optimal_parameter_evaluation(var_vector, p)
        y_prediction_exp = np.zeros((KrigingClass.x_data_scaled.shape[0], 1))
        for i in range(0, KrigingClass.x_data_scaled.shape[0]):
            cmt = (np.matmul(((np.abs(KrigingClass.x_data_scaled[i, :] - KrigingClass.x_data_scaled)) ** p), theta)).transpose()
            cov_matrix_tests = np.exp(-1 * cmt)
            y_prediction_exp[i, 0] = mean + np.matmul(np.matmul(cov_matrix_tests.transpose(), cov_inv), y_mu)
        
        ss_error, rmse_error, y_prediction = KrigingClass.error_calculation(theta, p, mean, cov_inv, y_mu,KrigingClass.x_data_scaled, KrigingClass.y_data)
        
        np.testing.assert_array_equal(y_prediction, y_prediction_exp)
        self.assertEqual(np.sum((KrigingClass.y_data-y_prediction_exp)**2)/KrigingClass.x_data_scaled.shape[0],ss_error)
        self.assertEqual(np.sqrt(np.sum((KrigingClass.y_data-y_prediction_exp)**2)/KrigingClass.x_data_scaled.shape[0]),rmse_error)

    
    
    def test_r2_calculation(self):
        KrigingClass = KrigingModel(self.training_data[0:3],regularization=False)
        p= 2
        var_vector = np.array([1,2,1.00000000e-06])
        theta, reg_param, mean, variance, cov_mat, cov_inv, y_mu = KrigingClass.optimal_parameter_evaluation(var_vector, p)
        
        ss_error, rmse_error, y_prediction = KrigingClass.error_calculation(theta, p, mean, cov_inv, y_mu,KrigingClass.x_data_scaled, KrigingClass.y_data)
        r_square = KrigingClass.r2_calculation(KrigingClass.y_data,y_prediction)
        assert 0.999999999999 == r_square

    
    def test_kriging_predict_output_01(self):
        np.random.seed(0)
        KrigingClass = KrigingModel(self.training_data)
        results = KrigingClass.kriging_training()
        y_pred = KrigingClass.kriging_predict_output(results, KrigingClass.x_data_scaled)
        assert y_pred.shape[0] == KrigingClass.x_data_scaled.shape[0]

    def test_kriging_predict_output(self):
        np.random.seed(0)
        KrigingClass = KrigingModel(self.training_data)
        results = KrigingClass.kriging_training()
        y_pred = KrigingClass.kriging_predict_output(results, np.array([0.1, 0.2]))
        assert y_pred.shape[0] == 1
        
    
    def test_kriging_training(self):
        KrigingClass = KrigingModel(self.training_data[0:3],regularization=False)

        np.random.seed(0)
        p = 2
        # Solve optimization problem

        bh_results = KrigingClass.parameter_optimization(p)
        # Calculate other variables and parameters
        optimal_theta, optimal_reg_param, optimal_mean, optimal_variance, optimal_cov_mat, opt_cov_inv, optimal_ymu = KrigingClass.optimal_parameter_evaluation(bh_results.x, p)
        # Training performance
        training_ss_error, rmse_error, y_training_predictions = KrigingClass.error_calculation(optimal_theta, p, optimal_mean, opt_cov_inv, optimal_ymu, KrigingClass.x_data_scaled, KrigingClass.y_data)
        r2_training = KrigingClass.r2_calculation(KrigingClass.y_data, y_training_predictions)
        
        np.random.seed(0)
        results = KrigingClass.kriging_training()
        np.testing.assert_array_equal(results.optimal_weights,optimal_theta)
        np.testing.assert_array_equal(results.regularization_parameter,optimal_reg_param)
        np.testing.assert_array_equal(results.optimal_mean,optimal_mean)
        np.testing.assert_array_equal(results.optimal_variance,optimal_variance)
        np.testing.assert_array_equal(results.optimal_covariance_matrix,optimal_cov_mat)
        np.testing.assert_array_equal(results.optimal_y_mu,optimal_ymu)
        np.testing.assert_array_equal(results.output_predictions,y_training_predictions)
        np.testing.assert_array_equal(results.training_R2,r2_training)
        np.testing.assert_array_equal(results.training_rmse,rmse_error)
        np.testing.assert_array_equal(results.optimal_p,p)
        np.testing.assert_array_equal(results.x_data,KrigingClass.x_data)
        np.testing.assert_array_equal(results.scaled_x,KrigingClass.x_data_scaled)
        np.testing.assert_array_equal(results.x_min,KrigingClass.x_data_min)
        np.testing.assert_array_equal(results.x_max,KrigingClass.x_data_max)
        
    
    def test_get_feature_vector_01(self):
        KrigingClass = KrigingModel(self.full_data,regularization=False)
        p = KrigingClass.get_feature_vector()
        expected_dict = {'x1': 0, 'x2': 0}
        assert expected_dict == p.extract_values()
    
    def test_get_feature_vector_02(self):
        KrigingClass = KrigingModel(self.training_data,regularization=False)
        p = KrigingClass.get_feature_vector()
        expected_dict = {0: 0, 1: 0}
        assert expected_dict == p.extract_values()


    def test_kriging_generate_expression(self):
        KrigingClass = KrigingModel(self.training_data,regularization=False)
        results = KrigingClass.kriging_training()
        p = KrigingClass.get_feature_vector()
        lv =[]
        for i in p.keys():
            lv.append(p[i])
        rbf_expr = results.kriging_generate_expression((lv))
        
        
if __name__ == '__main__':
    unittest.main()

