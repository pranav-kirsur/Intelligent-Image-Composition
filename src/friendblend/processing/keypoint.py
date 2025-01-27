"""
Contains code for keypoint detection and matching
"""

import logging
import sys

import cv2 as cv
import numpy as np

from friendblend.processing.helpers import pt_in_box
from friendblend.helpers import imshow

__all__ = ["ORB", "filter_keypoints", "find_homography"]


class ORB:
    """
    Wrapper over opencv ORB
    """

    def __init__(self, img, n_keypoints=1000):
        self.n_keypoints = n_keypoints
        self.orb = None
        self.img = img.copy()

    def get_keypoints(self):
        """
        Returns ORB keypoints
        """
        if self.orb is None:
            self.orb = cv.ORB_create(nfeatures=self.n_keypoints)

        return self.orb.detect(self.img)

    def get_descriptors(self, kps):
        """
        Returns ORB descriptors
        """
        return self.orb.compute(self.img, kps)[1]


def filter_keypoints(box1, box2, kps):
    """
    Only returns keypoints which are NOT in box1 or box2
    """
    return list(
        filter(
            lambda kp: not pt_in_box(kp.pt, box1) and not pt_in_box(kp.pt, box2),
            kps.copy(),
        )
    )


def find_homography(kps1, ds1, kps2, ds2, img1, img2, max_distance=30):
    """
    Uses bruteforce matcher with hamming distance to compute homography
    fails if matches found are less than `min_matches`
    """
    log = logging.getLogger()

    # Get matches using BFMatcher
    matches = cv.BFMatcher(cv.NORM_HAMMING, crossCheck=True).match(ds1, ds2)
    matches = list(filter(lambda x: x.distance < max_distance, matches))

    src = []
    dest = []

    for match in matches:
        src.append(kps1[match.queryIdx].pt)
        dest.append(kps2[match.trainIdx].pt)

    src = np.array(src).reshape((-1, 1, 2))
    dest = np.array(dest).reshape((-1, 1, 2))

    matched_img = cv.drawMatches(img1, kps1, img2, kps2, matches, None)

    # Compute homography
    H, mask = cv.findHomography(src, dest, cv.RANSAC)

    if not mask.any():
        log.error("Couldn't compute homography")
        sys.exit(1)

    return H, matched_img
