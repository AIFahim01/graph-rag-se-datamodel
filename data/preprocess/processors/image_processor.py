from typing import List, Sequence

from PIL import Image
from vllm import LLM, SamplingParams
from vllm.inputs.data import PromptType
from vllm.model_executor.models.deepseek_ocr import NGramPerReqLogitsProcessor


class VllmImageExtractor:
    def __init__(
        self,
        model_name: str = "deepseek-ai/DeepSeek-OCR",
        prompt: str = "<image>\nDescribe the image with technical context.",
    ) -> None:
        self.llm = LLM(
            model=model_name,
            enable_prefix_caching=True,
            mm_processor_cache_gb=0,
            logits_processors=[NGramPerReqLogitsProcessor],
        )
        self.prompt = prompt
        self.sampling_params = SamplingParams(
            temperature=0.0,
            max_tokens=8192,
            extra_args=dict(
                ngram_size=30,
                window_size=90,
                whitelist_token_ids={128821, 128822},
            ),
            skip_special_tokens=False,
        )

    def _build_inputs(self, images: Sequence[Image.Image]) -> List[PromptType]:
        model_inputs: List[PromptType] = []
        for img in images:
            if not isinstance(img, Image.Image):
                raise TypeError("All inputs must be PIL.Image.Image instances.")
            if img.mode != "RGB":
                img = img.convert("RGB")

            model_inputs.append(
                {
                    "prompt": self.prompt,
                    "multi_modal_data": {"image": img},
                }
            )
        return model_inputs

    def _extract_batch(self, images: Sequence[Image.Image]) -> List[str]:
        model_inputs = self._build_inputs(images)
        outputs = self.llm.generate(model_inputs, self.sampling_params)

        texts: List[str] = []
        for output in outputs:
            chunks = [chunk.text for chunk in output.outputs]
            texts.append("".join(chunks))
        return texts

    def extract_image(self, image: Image.Image) -> str:
        """Extract OCR text from a single PIL image."""
        return self._extract_batch([image])[0]

    def extract_images(self, images: Sequence[Image.Image]) -> List[str]:
        """Extract OCR text from multiple PIL images."""
        return self._extract_batch(images)


# Prepare batched input with your image file
# image_1 = Image.open("path_to_your_image_1.png").convert("RGB")
# image_2 = Image.open("path_to_your_image_2.png").convert("RGB")

# prompt = str(
#     "<image>\nDescribe the image with technical context."
# )

# extractor = VllmImageExtractor(prompt=prompt)

# output1 = extractor.extract_image(image_1)
# print("OCR Output for image 1:", output1)
# output2 = extractor.extract_images([image_1, image_2])
# for op in output2:
#     print("OCR Output in batch:", op)