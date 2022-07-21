# coding=utf-8

import json
import os

import datasets

from layoutlmft.data.utils import load_image, normalize_bbox


logger = datasets.logging.get_logger(__name__)


_CITATION = """\
@article{Jaume2019FUNSDAD,
  title={FUNSD: A Dataset for Form Understanding in Noisy Scanned Documents},
  author={Guillaume Jaume and H. K. Ekenel and J. Thiran},
  journal={2019 International Conference on Document Analysis and Recognition Workshops (ICDARW)},
  year={2019},
  volume={2},
  pages={1-6}
}
"""

_DESCRIPTION = """\
https://guillaumejaume.github.io/FUNSD/
"""


class InvoiceConfig(datasets.BuilderConfig):
    """BuilderConfig for INVOICE"""

    def __init__(self, **kwargs):
        """BuilderConfig for INVOICE.

        Args:
          **kwargs: keyword arguments forwarded to super.
        """
        super(InvoiceConfig, self).__init__(**kwargs)


class Invoice(datasets.GeneratorBasedBuilder):
    """Conll2003 dataset."""

    BUILDER_CONFIGS = [
        InvoiceConfig(name="invoice", version=datasets.Version("1.0.0"), description="INVOICE dataset"),
    ]

    def _info(self):
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=datasets.Features(
                {
                    "id": datasets.Value("string"),
                    "tokens": datasets.Sequence(datasets.Value("string")),
                    "bboxes": datasets.Sequence(datasets.Sequence(datasets.Value("int64"))),
                    "ner_tags": datasets.Sequence(
                        datasets.features.ClassLabel(
                            names=["O", "B-OTHER", "I-OTHER", "B-SUPPLIER_NAME", "I-SUPPLIER_NAME", "B-SUPPLIER_ADDR", "I-SUPPLIER_ADDR", "B-TOTALAMOUNT", "I-TOTALAMOUNT"]
                        )
                    ),
                    "image": datasets.Array3D(shape=(3, 224, 224), dtype="uint8"),
                }
            ),
            supervised_keys=None,
            # homepage="https://guillaumejaume.github.io/FUNSD/",
            # citation=_CITATION,
        )

    def _split_generators(self, dl_manager):
        """Returns SplitGenerators."""
        downloaded_file = "/media/minh/Storage/projects/EGS/InvoiceDataExtraction/20220516_invoice_data"
        return [
            datasets.SplitGenerator(
                name=datasets.Split.TRAIN, gen_kwargs={"filepath": f"{downloaded_file}/training_data/"}
            ),
            datasets.SplitGenerator(
                name=datasets.Split.VALIDATION, gen_kwargs={"filepath": f"{downloaded_file}/testing_data/"}
            ),
            datasets.SplitGenerator(
                name=datasets.Split.TEST, gen_kwargs={"filepath": f"{downloaded_file}/testing_data/"}
            ),
        ]

    def _generate_examples(self, filepath):
        logger.info("⏳ Generating examples from = %s", filepath)
        ann_dir = os.path.join(filepath, "annotations")
        img_dir = os.path.join(filepath, "images")
        for guid, file in enumerate(sorted(os.listdir(ann_dir))):
            tokens = []
            bboxes = []
            ner_tags = []

            file_path = os.path.join(ann_dir, file)
            with open(file_path, "r", encoding="utf8") as f:
                data = json.load(f)
            image_path = os.path.join(img_dir, file)
            image_path = image_path.replace("json", "jpg")
            image, size = load_image(image_path)
            for item in data["form"]:
                words, label = item["words"], item["label"]
                words = [w for w in words if w["text"].strip() != ""]
                if len(words) == 0:
                    continue
                if label == "other":
                    for w in words:
                        tokens.append(w["text"])
                        ner_tags.append("O")
                        bboxes.append(normalize_bbox(w["box"], size))
                else:
                    tokens.append(words[0]["text"])
                    ner_tags.append("B-" + label.upper())
                    bboxes.append(normalize_bbox(words[0]["box"], size))
                    for w in words[1:]:
                        tokens.append(w["text"])
                        ner_tags.append("I-" + label.upper())
                        bboxes.append(normalize_bbox(w["box"], size))

            yield guid, {"id": str(guid), "tokens": tokens, "bboxes": bboxes, "ner_tags": ner_tags, "image": image}
