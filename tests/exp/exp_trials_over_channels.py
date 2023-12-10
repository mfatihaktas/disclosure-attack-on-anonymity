from src.model import trials_over_channels


if __name__ == "__main__":
    n = 100
    m = 1
    # m = 20
    # m = n
    # k = 10
    k = 1000
    # p = 0.1
    # p = 0.5
    p = 0.9
    num_samples = 100

    trials_over_channels.plot_sorted_num_trials_over_channels(
        n=n, m=m, k=k, p=p, num_samples=num_samples
    )
