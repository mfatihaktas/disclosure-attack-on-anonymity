import numpy
import sklearn.cluster

from src.debug_utils import log, DEBUG, INFO


def test_sklearn_kmeans():
    data = [
        ["s0", 0.2],
        ["s1", 0.04],
        ["s2", -0.01],
    ]
    array = numpy.array([[x[1]] for x in data])
    (centroids, labels, intertia) = sklearn.cluster.k_means(array, 2)

    for i in range(len(data)):
        log(
            INFO, f">> i= {i}",
            data=data[i],
            label=labels[i],
            # centroid=centroids[i],
        )
