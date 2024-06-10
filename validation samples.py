from typing import Optional, Any
from pydantic import BaseModel, ValidationError, Field, ConfigDict, HttpUrl, model_validator, field_validator


class ValidationBaseModel(BaseModel):
    model_config = ConfigDict(
            # use_enum_values=True,  # используем значение из Enum
            # validate_assignment=True,  # включаем валидацию при изменении
            # extra='allow',
            extra='ignore',
        )


# ------------------------------------------- prices





class Prices_Attributes(ValidationBaseModel):
    mainAllergens: list[str] = None
    customTags: list[str] = None

class Prices_Options(ValidationBaseModel):
    attributes: dict[str, list[str]] = {}
    pricePerCount: int = None
    incrementStep: float = None
    quantityType: str = None

class Prices_DiscountPricing(ValidationBaseModel):
    discountPricing: int = Field(default=None, alias='price')
    bundleDiscountDesc: str = None
    
class Prices_Pricing(ValidationBaseModel):
    price: int = None

class Prices_SnippetImage(ValidationBaseModel):
    url: str = None

class Prices_Data_Categories_Items_Items_Value(ValidationBaseModel):
    sku_id: str = Field(alias='id')
    sku_name: str = Field(alias='title')
    deepLink: str = None
    quantityLimit: int = None
    amount: str = None
    pricing: Prices_Pricing = Prices_Pricing()
    discountPricing: Prices_DiscountPricing = Prices_DiscountPricing()
    options: Prices_Options = Prices_Options()
    snippetImage: Prices_SnippetImage = Prices_SnippetImage()
    Brand: Optional[str] = Field(default=None, alias='privateLabelBrand')
    # imageSize: list[int]

class Prices_Data_Categories_Items_Items(ValidationBaseModel):
    vis_2: int = Field(alias='index')
    value: Prices_Data_Categories_Items_Items_Value
    # items: Any # ????

class Prices_Data_Categories_Items_Value(ValidationBaseModel):
    tk3_id: str = Field(alias='id')
    tk3_name: str = Field(alias='title')

class Prices_Data_Categories_Items(ValidationBaseModel):
    vis_1: int = Field(alias='index')
    value: Prices_Data_Categories_Items_Value
    items: list[Prices_Data_Categories_Items_Items]
    @field_validator('items')
    def check_non_empty_items(cls, items):
        if items is None or not items:
            raise ValueError('items second list cannot be empty')
        return items

class Prices_Data_Categories_Value(ValidationBaseModel):
    tk2_id: str = Field(alias='id')
    tk2_name: str = Field(alias='title')

class Prices_Data_Categories(ValidationBaseModel):
    value: Prices_Data_Categories_Value
    items: list[Prices_Data_Categories_Items]

    @field_validator('items')
    def check_non_empty_items(cls, items):
        if items is None or not items:
            raise ValueError('items first list cannot be empty')
        return items


class Prices_CategoryGroup(ValidationBaseModel):
    tk1_id: str = Field(alias='id')
    tk1_name: str = Field(alias='title')

class Prices_Data(ValidationBaseModel):
    categories: list[Prices_Data_Categories]
    yaTraceId: str
    offerId: str
    layoutId: str
    categoryGroup: Prices_CategoryGroup
        
class ValidationPrices(ValidationBaseModel):
    data: Prices_Data



# ------------------------------------------- category
class Category_Items2(ValidationBaseModel):
    category_id: str = Field(alias='id')

class Category_Items(ValidationBaseModel):
    category_group_id: str = Field(alias='id')
    items: list[Category_Items2]

class Category_Products(ValidationBaseModel):
    product_cat_id: str = Field(alias='id')
    product_cat_title: str = Field(alias='title')

class Category_Modes(ValidationBaseModel):
    items: list[Category_Items]

class Category_Field_data(ValidationBaseModel):
    modes: list[Category_Modes]
    # products: list[Category_Products]
    layoutId: str

class ValidationCategory(ValidationBaseModel):
    data: Category_Field_data