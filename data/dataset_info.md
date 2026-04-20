# Dataset Information

## Sign Language MNIST

| Property | Value |
|---|---|
| Source | [Kaggle — Sign Language MNIST](https://www.kaggle.com/datasets/datamunge/sign-language-mnist) |
| Format | CSV (pixel values, 28×28 grayscale) |
| Training samples | 27,455 |
| Test samples | 7,172 |
| Classes | 24 (ASL A–Y, excluding J & Z which require motion) |
| Image size (raw) | 28×28 pixels |
| Image size (model input) | 64×64 pixels (resized in data_loader.py) |

## How to Download

1. Create a Kaggle account at https://www.kaggle.com
2. Go to https://www.kaggle.com/datasets/datamunge/sign-language-mnist
3. Click **Download** → extract the archive
4. Place the files here:
   ```
   data/raw/sign_mnist_train.csv
   data/raw/sign_mnist_test.csv
   ```

## Class Distribution

The dataset is approximately balanced across all 24 classes,
with roughly 1,000–1,300 samples per class in the training set.

## Label Mapping

| Index | Letter |   | Index | Letter |
|-------|--------|---|-------|--------|
| 0     | A      |   | 12    | N      |
| 1     | B      |   | 13    | O      |
| 2     | C      |   | 14    | P      |
| 3     | D      |   | 15    | Q      |
| 4     | E      |   | 16    | R      |
| 5     | F      |   | 17    | S      |
| 6     | G      |   | 18    | T      |
| 7     | H      |   | 19    | U      |
| 8     | I      |   | 20    | V      |
| 9     | K      |   | 21    | W      |
| 10    | L      |   | 22    | X      |
| 11    | M      |   | 23    | Y      |

> **Note**: J (index 9 in the original dataset) and Z (index 25) are excluded
> because they involve hand motion rather than static poses.
