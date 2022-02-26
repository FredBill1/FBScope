"https://github.com/ros-perception/image_pipeline.git"

import numpy as np
import cv2 as cv
import math
from typing import List, Tuple
from enum import Enum


def _pdist(p1: List[float], p2: List[float]):
    """
    Distance bwt two points. p1 = (x, y), p2 = (x, y)
    """
    d1, d2 = p1[0] - p2[0], p1[1] - p2[1]
    return math.sqrt(d1 * d1 + d2 * d2)


class ChessboardInfo:
    def __init__(self, n_cols=0, n_rows=0):
        self.n_cols = max(n_cols, n_rows)
        self.n_rows = min(n_cols, n_rows)


class CAMERA_MODEL(Enum):
    PINHOLE = 0
    FISHEYE = 1


def _get_corners(img: np.ndarray, board: ChessboardInfo, refine=True, checkerboard_flags=0) -> Tuple[bool, np.ndarray]:
    """
    Get corners for a particular chessboard for an image
    """
    h = img.shape[0]
    w = img.shape[1]
    if len(img.shape) == 3 and img.shape[2] == 3:
        mono = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    else:
        mono = img

    ret = cv.findChessboardCorners(
        mono,
        (board.n_cols, board.n_rows),
        flags=cv.CALIB_CB_ADAPTIVE_THRESH | cv.CALIB_CB_NORMALIZE_IMAGE | checkerboard_flags,
    )
    ok: bool = ret[0]
    corners: np.ndarray = ret[1]

    if not ok:
        return (ok, corners)

    # If any corners are within BORDER pixels of the screen edge, reject the detection by setting ok to false
    # NOTE: This may cause problems with very low-resolution cameras, where 8 pixels is a non-negligible fraction
    # of the image size. See http://answers.ros.org/question/3155/how-can-i-calibrate-low-resolution-cameras
    BORDER = 8
    if not all(
        [
            (BORDER < corners[i, 0, 0] < (w - BORDER)) and (BORDER < corners[i, 0, 1] < (h - BORDER))
            for i in range(corners.shape[0])
        ]
    ):
        ok = False

    # Ensure that all corner-arrays are going from top to bottom.
    if board.n_rows != board.n_cols:
        if corners[0, 0, 1] > corners[-1, 0, 1]:
            corners = np.copy(np.flipud(corners))
    else:
        direction_corners = (corners[-1] - corners[0]) >= np.array([[0.0, 0.0]])

        if not np.all(direction_corners):
            if not np.any(direction_corners):
                corners = np.copy(np.flipud(corners))
            elif direction_corners[0][0]:
                corners = np.rot90(corners.reshape(board.n_rows, board.n_cols, 2)).reshape(
                    board.n_cols * board.n_rows, 1, 2
                )
            else:
                corners = np.rot90(corners.reshape(board.n_rows, board.n_cols, 2), 3).reshape(
                    board.n_cols * board.n_rows, 1, 2
                )

    if refine and ok:
        # Use a radius of half the minimum distance between corners. This should be large enough to snap to the
        # correct corner, but not so large as to include a wrong corner in the search window.
        min_distance = float("inf")
        for row in range(board.n_rows):
            for col in range(board.n_cols - 1):
                index = row * board.n_rows + col
                min_distance = min(min_distance, _pdist(corners[index, 0], corners[index + 1, 0]))
        for row in range(board.n_rows - 1):
            for col in range(board.n_cols):
                index = row * board.n_rows + col
                min_distance = min(min_distance, _pdist(corners[index, 0], corners[index + board.n_cols, 0]))
        radius = int(math.ceil(min_distance * 0.5))
        cv.cornerSubPix(
            mono, corners, (radius, radius), (-1, -1), (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.1)
        )

    return (ok, corners)


class MonoCalibrator:
    def __init__(self, boards: List[ChessboardInfo], fisheye_flags=0, checkerboard_flags=cv.CALIB_CB_FAST_CHECK):
        self._boards: List[ChessboardInfo] = boards
        self.camera_model: CAMERA_MODEL = CAMERA_MODEL.PINHOLE
        self.fisheye_calib_flags = fisheye_flags
        self.checkerboard_flags = checkerboard_flags

    def cal(self, images: List[np.ndarray]):
        """
        Calibrate camera from given images
        """
        goodcorners = self.collect_corners(images)
        self.cal_fromcorners(goodcorners)
        self.calibrated = True

    def collect_corners(self, images: List[np.ndarray]):
        self.size = (images[0].shape[1], images[0].shape[0])
        corners = [self.get_corners(i) for i in images]

        goodcorners = [(co, b) for (ok, co, b) in corners if ok]
        if not goodcorners:
            raise RuntimeError("No corners found in images!")
        return goodcorners

    def get_corners(
        self, img: np.ndarray, refine: bool = True, show: bool = False
    ) -> Tuple[bool, np.ndarray, ChessboardInfo]:
        for b in self._boards:
            (ok, corners) = _get_corners(img, b, refine, self.checkerboard_flags)
            if ok:
                if show:
                    color = cv.cvtColor(img, cv.COLOR_GRAY2BGR)
                    cv.drawChessboardCorners(color, (b.n_cols, b.n_rows), corners, True)
                    cv.imshow("corners", color)
                    cv.waitKey(0)
                return (ok, corners, b)
        if show:
            cv.imshow("corners", img)
            cv.waitKey(0)
        return (False, None, None)

    def cal_fromcorners(self, good: List[Tuple[np.ndarray, ChessboardInfo]]):
        """
        :param good: Good corner positions and boards
        :type good: [(corners, ChessboardInfo)]
        """

        (ipts, boards) = zip(*good)
        opts = self.mk_object_points(boards)
        # If FIX_ASPECT_RATIO flag set, enforce focal lengths have 1/1 ratio
        intrinsics_in = np.eye(3, dtype=np.float64)

        if self.camera_model == CAMERA_MODEL.PINHOLE:
            print("mono pinhole calibration...")
            reproj_err, self.intrinsics, dist_coeffs, rvecs, tvecs = cv.calibrateCamera(
                opts, ipts, self.size, None, None,
            )
            # OpenCV returns more than 8 coefficients (the additional ones all zeros) when CALIB_RATIONAL_MODEL is set.
            # The extra ones include e.g. thin prism coefficients, which we are not interested in.
            self.distortion = dist_coeffs.flat[:8].reshape(-1, 1)
        elif self.camera_model == CAMERA_MODEL.FISHEYE:
            print("mono fisheye calibration...")
            # WARNING: cv.fisheye.calibrate wants float64 points
            ipts64 = np.asarray(ipts, dtype=np.float64)
            ipts = ipts64
            opts64 = np.asarray(opts, dtype=np.float64)
            opts = opts64
            reproj_err, self.intrinsics, self.distortion, rvecs, tvecs = cv.fisheye.calibrate(
                opts, ipts, self.size, intrinsics_in, None, flags=self.fisheye_calib_flags
            )

        # R is identity matrix for monocular calibration
        self.R = np.eye(3, dtype=np.float64)
        self.P = np.zeros((3, 4), dtype=np.float64)

        self.set_alpha(0.0)

    def mk_object_points(self, boards: List[ChessboardInfo]) -> List[np.ndarray]:
        opts = []
        for b in boards:
            objp = np.zeros((b.n_cols * b.n_rows, 3), np.float32)
            objp[:, :2] = np.mgrid[0 : b.n_cols, 0 : b.n_rows].T.reshape(-1, 2)
            opts.append(objp)
        return opts

    def set_alpha(self, a: float):
        """
        Set the alpha value for the calibrated camera solution.  The alpha
        value is a zoom, and ranges from 0 (zoomed in, all pixels in
        calibrated image are valid) to 1 (zoomed out, all pixels in
        original image are in calibrated image).
        """

        if self.camera_model == CAMERA_MODEL.PINHOLE:
            # NOTE: Prior to Electric, this code was broken such that we never actually saved the new
            # camera matrix. In effect, this enforced P = [K|0] for monocular cameras.
            # TODO: Verify that OpenCV #1199 gets applied (improved GetOptimalNewCameraMatrix)
            ncm, _ = cv.getOptimalNewCameraMatrix(self.intrinsics, self.distortion, self.size, a)
            for j in range(3):
                for i in range(3):
                    self.P[j, i] = ncm[j, i]
            self.mapx, self.mapy = cv.initUndistortRectifyMap(
                self.intrinsics, self.distortion, self.R, ncm, self.size, cv.CV_32FC1
            )
        elif self.camera_model == CAMERA_MODEL.FISHEYE:
            # NOTE: estimateNewCameraMatrixForUndistortRectify not producing proper results, using a naive approach instead:
            self.P[:3, :3] = self.intrinsics[:3, :3]
            self.P[0, 0] /= 1.0 + a
            self.P[1, 1] /= 1.0 + a
            self.mapx, self.mapy = cv.fisheye.initUndistortRectifyMap(
                self.intrinsics, self.distortion, self.R, self.P, self.size, cv.CV_32FC1
            )

    def show(self):
        "D K R P"
        print(self.distortion, self.intrinsics, self.R, self.P, sep="\n")

    def undistort_points(self, src):
        """
        :param src: N source pixel points (u,v) as an Nx2 matrix
        :type src: :class:`cvMat`

        Apply the post-calibration undistortion to the source points
        """
        if self.camera_model == CAMERA_MODEL.PINHOLE:
            return cv.undistortPoints(src, self.intrinsics, self.distortion, R=self.R, P=self.P)
        elif self.camera_model == CAMERA_MODEL.FISHEYE:
            return cv.fisheye.undistortPoints(src, self.intrinsics, self.distortion, R=self.R, P=self.P)

    def remap(self, img: np.ndarray) -> np.ndarray:
        return cv.remap(img, self.mapx, self.mapy, cv.INTER_LINEAR)


__all__ = ["ChessboardInfo", "CAMERA_MODEL", "MonoCalibrator"]

if __name__ == "__main__":
    from glob import glob
    from os.path import join
    import os

    DIR = "D:/CarImg"
    EXT = ".png"

    calibrator = MonoCalibrator([ChessboardInfo(8, 6)])

    # dirs = glob(join(DIR, "*" + EXT))
    # for d in dirs:
    #     img = cv.imread(d, cv.IMREAD_GRAYSCALE)
    #     ret, _, _ = calibrator.get_corners(img)
    #     if not ret:
    #         print(d)
    #         os.remove(d)

    dirs = glob(join(DIR, "*" + EXT))
    imgs = [cv.imread(d, cv.IMREAD_GRAYSCALE) for d in dirs]
    calibrator.cal(imgs)
    calibrator.show()
    for img in imgs:
        rect = calibrator.remap(img)
        cv.imshow("img", np.hstack((img, rect)))
        if cv.waitKey(0) == 27:  # esc
            break

