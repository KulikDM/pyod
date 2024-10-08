# -*- coding: utf-8 -*-
"""
Median Absolute deviation (MAD) Algorithm.
Strictly for Univariate Data.
"""
# Author: Yahya Almardeny <almardeny@gmail.com>
# License: BSD 2 clause


import numpy as np
from sklearn.utils import check_array

from .base import BaseDetector


def _check_dim(X):
    """
    Internal function to assert univariate data
    """
    if X.shape[1] != 1:
        raise ValueError('MAD algorithm is just for univariate data. '
                         'Got Data with {} Dimensions.'.format(X.shape[1]))


class MAD(BaseDetector):
    """Median Absolute Deviation: for measuring the distances between
    data points and the median in terms of median distance.
    See :cite:`iglewicz1993detect` for details.

    Parameters
    ----------
    threshold : float, optional (default=3.5)
       The modified z-score to use as a threshold. Observations with
       a modified z-score (based on the median absolute deviation) greater
       than this value will be classified as outliers.

    Attributes
    ----------
    decision_scores_ : numpy array of shape (n_samples,)
        The outlier scores of the training data.
        The higher, the more abnormal. Outliers tend to have higher
        scores. This value is available once the detector is
        fitted.

    threshold_ : float
       The modified z-score to use as a threshold. Observations with
       a modified z-score (based on the median absolute deviation) greater
       than this value will be classified as outliers.

    labels_ : int, either 0 or 1
        The binary labels of the training data. 0 stands for inliers
        and 1 for outliers/anomalies. It is generated by applying
        ``threshold_`` on ``decision_scores_``.
    """

    def __init__(self, threshold=3.5, contamination=0.1):
        super(MAD, self).__init__(contamination=contamination)
        if not isinstance(threshold, (float, int)):
            raise TypeError(
                'threshold must be a number. Got {}'.format(type(threshold)))
        self.threshold = threshold

    def fit(self, X, y=None):
        """Fit detector. y is ignored in unsupervised methods.

        Parameters
        ----------
        X : numpy array of shape (n_samples, n_features)
            The input samples. Note that `n_features` must equal 1.

        y : Ignored
            Not used, present for API consistency by convention.

        Returns
        -------
        self : object
            Fitted estimator.
        """
        X = check_array(X, ensure_2d=False, force_all_finite=False)
        _check_dim(X)
        self._set_n_classes(y)
        self.threshold_ = self.threshold
        self.median_ = None  # reset median after each call
        self.median_diff_ = None  # reset median_diff after each call
        self.decision_scores_ = self.decision_function(X)
        self._process_decision_scores()

        return self

    def decision_function(self, X):
        """Predict raw anomaly score of X using the fitted detector.
        The anomaly score of an input sample is computed based on different
        detector algorithms. For consistency, outliers are assigned with
        larger anomaly scores.

        Parameters
        ----------
        X : numpy array of shape (n_samples, n_features)
            The training input samples. Sparse matrices are accepted only
            if they are supported by the base estimator.
            Note that `n_features` must equal 1.

        Returns
        -------
        anomaly_scores : numpy array of shape (n_samples,)
            The anomaly score of the input samples.
        """
        X = check_array(X, ensure_2d=False, force_all_finite=False)
        _check_dim(X)
        return self._mad(X)

    def _mad(self, X):
        """
        Apply the robust median absolute deviation (MAD)
        to measure the distances of data points from the median.

        Returns
        -------
        numpy array containing modified Z-scores of the observations.
        The greater the score, the greater the outlierness.
        """
        obs = np.reshape(X, (-1, 1))
        # `self.median` will be None only before `fit()` is called
        self.median_ = np.nanmedian(
            obs) if self.median_ is None else self.median_
        diff = np.abs(obs - self.median_)
        self.median_diff_ = np.nanmedian(
            diff) if self.median_diff_ is None else self.median_diff_
        return np.nan_to_num(np.ravel(0.6745 * diff / self.median_diff_))

    def _process_decision_scores(self):
        """This overrides PyOD base class function in order to use the
        proper `threshold_` which is quite different in the base class.
        Internal function to calculate key attributes:
        - labels_: binary labels of training data.
        - _mu: mean of decision scores.
        - _sigma: standard deviation of decision scores.

        Returns
        -------
        self
        """
        self.labels_ = (self.decision_scores_ > self.threshold).astype(
            'int').ravel()

        # calculate for predict_proba()
        self._mu = np.nanmean(self.decision_scores_)
        self._sigma = np.nanstd(self.decision_scores_)

        return self
