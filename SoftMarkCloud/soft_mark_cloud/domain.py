from typing import Any, List


class DisplayField:
    field_type = None

    def __init__(self, name: str, value: Any):
        self.name = name
        self.value = value

    @property
    def json(self):
        return {
            "name": self.name,
            "type": self.field_type,
            "value": self.value
        }


class StringField(DisplayField):
    field_type = 'string'

    def __init__(self, name: str, value: str):
        super(StringField, self).__init__(name, str(value))


class ItemsField(DisplayField):
    field_type = 'items'

    def __init__(self, name: str, value: List['DisplayItem']):
        super(ItemsField, self).__init__(name, value)

    @property
    def json(self):
        return {
            "name": self.name,
            "type": self.field_type,
            "value": [item.json for item in self.value]
        }


class DisplayItem:
    def __init__(self, name: str, item_type: str, fields: List[DisplayField] = None):
        self.name = name
        self.item_type = item_type
        self.fields = fields or []

    @property
    def json(self):
        return {
            "name": self.name,
            "item_type": self.item_type,
            "fields": [f.json for f in self.fields]
        }
