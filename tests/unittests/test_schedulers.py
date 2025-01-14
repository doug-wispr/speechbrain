def test_NewBobScheduler():

    from speechbrain_experimental.nnet.schedulers import NewBobScheduler

    scheduler = NewBobScheduler(initial_value=0.8)

    prev_lr, next_lr = scheduler(1.0)
    assert prev_lr == 0.8
    assert next_lr == 0.8

    prev_lr, next_lr = scheduler(1.1)
    assert next_lr == 0.4

    prev_lr, next_lr = scheduler(0.5)
    assert next_lr == 0.4

    scheduler = NewBobScheduler(initial_value=0.8, patient=3)
    prev_lr, next_lr = scheduler(1.0)
    assert next_lr == 0.8

    prev_lr, next_lr = scheduler(1.1)
    prev_lr, next_lr = scheduler(1.1)
    prev_lr, next_lr = scheduler(1.1)
    assert next_lr == 0.8

    prev_lr, next_lr = scheduler(1.1)
    assert next_lr == 0.4
    assert scheduler.current_patient == 3


def test_WarmAndExpDecayLRSchedule():

    from speechbrain_experimental.nnet.schedulers import WarmAndExpDecayLRSchedule
    from speechbrain_experimental.nnet.linear import Linear
    import torch

    model = Linear(input_size=3, n_neurons=4)
    optim = torch.optim.Adam(model.parameters(), lr=1)
    scheduler = WarmAndExpDecayLRSchedule(
        lr=1, n_warmup_steps=2, decay_factor=0.01, total_steps=6
    )

    scheduler(optim)
    assert optim.param_groups[0]["lr"] == 0.0

    scheduler(optim)
    assert optim.param_groups[0]["lr"] == 0.5

    scheduler(optim)
    assert optim.param_groups[0]["lr"] == 1

    scheduler(optim)
    assert optim.param_groups[0]["lr"] == 0.31622776601683794
