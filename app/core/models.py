import datetime
import json
from pathlib import Path
from typing import Any

import pydantic
from pydantic_core import core_schema


class VideoPoint:
    def __init__(self, value: str):
        self.value = datetime.time.fromisoformat(value)

    def __lt__(self, other):
        return self.value < other.value

    def __str__(self):
        return self.value.isoformat()

    @classmethod
    def validate(cls, value: Any, handler, info: pydantic.ValidationInfo):
        return cls(str(value))

    @classmethod
    def __get_pydantic_core_schema__(cls,
                                     source_type: Any,
                                     handler: pydantic.GetCoreSchemaHandler):
        return core_schema.with_info_wrap_validator_function(
            cls.validate,
            handler(str),
            field_name=handler.field_name,
            serialization=core_schema.PlainSerializerFunctionSerSchema(
                function=str,
                type='function-plain'
            )
        )


class VideoPieceModel(pydantic.BaseModel):
    file_id: int
    start: VideoPoint
    end: VideoPoint


class VideoModel(pydantic.BaseModel):
    name: str = ""
    video_name: str = ""
    video_description: str = ""
    piece_list: list[VideoPieceModel] = []
    video_input: list[Path] = []


class VideoOutput:
    def __init__(self, number: int):
        self.number = number
        self.model = VideoModel()

    def is_exists(self):
        return self.info_file.exists()

    @property
    def video_folder(self) -> Path:
        root = Path("~/Videos/ffmpeg").expanduser()
        return root / self._cell(100) / self._cell(10) / self._cell(1)

    @property
    def info_file(self):
        return self.video_folder / 'info.json'

    def update_meta(self, name="", video_name="", video_description=""):
        updated = {
            'name': name,
            'video_name': video_name,
            'video_description': video_description
        }
        updated = {
            k: v
            for k, v in updated.items()
            if v
        }
        self.model.model_copy(update=updated)

    def save(self):
        self.video_folder.mkdir(parents=True, exist_ok=True)
        self.info_file.write_text(json.dumps(self.model.model_dump(mode='json')))

    def load(self):
        info = json.loads(self.info_file.read_text())
        self.model = VideoModel.model_validate(info)

    def is_valid_file_id(self, file_id):
        return 0 <= file_id < len(self.model.video_input)

    def add_video_input(self, filename):
        current_index = len(self.model.video_input)
        self.model.video_input.append(filename)
        return current_index

    def add_piece(self, piece: VideoPieceModel):
        assert self.is_valid_file_id(piece.file_id)

        self.model.piece_list.append(piece)

    def _cell(self, u: int) -> str:
        ceil_num = self.number // u * u
        return f'{ceil_num:03}'
