import dotenv
import openai
import numpy as np
from baml_client.sync_client import b
from baml_client.type_builder import TypeBuilder
from baml_client.tracing import trace
from pydantic import BaseModel

dotenv.load_dotenv()
client = openai.OpenAI()


class Category(BaseModel):
    name: str
    embedding_text: str
    llm_description: str


def load_categories() -> list[Category]:
    return [
        Category(name="Search Products", embedding_text="Find products", llm_description="User is looking to search for products"),
        Category(name="Buy Product", embedding_text="do something with money", llm_description="User is looking to buy a product"),
        Category(name="View Product Details", embedding_text="Product details", llm_description="User wants to view detailed information about a product"),
        Category(name="Add to Cart", embedding_text="Add item to cart", llm_description="User intends to add a product to their shopping cart"),
        Category(name="Checkout", embedding_text="Proceed to checkout", llm_description="User is ready to purchase and wants to checkout"),
        Category(name="Apply Discount Code", embedding_text="Use discount code", llm_description="User wants to apply a discount code to their purchase"),
        Category(name="Track Order", embedding_text="Order tracking", llm_description="User wants to track the status of their order"),
        Category(name="Return Item", embedding_text="Return product", llm_description="User wants to return a purchased item"),
        Category(name="Contact Support", embedding_text="Customer support", llm_description="User needs assistance from customer support"),
        Category(name="Read Reviews", embedding_text="Product reviews", llm_description="User wants to read reviews about a product"),
        Category(name="Compare Products", embedding_text="Compare items", llm_description="User is comparing different products"),
        Category(name="View Wishlist", embedding_text="Wishlist", llm_description="User wants to view their wishlist"),
        Category(name="Search Deals", embedding_text="Find deals", llm_description="User is looking for deals or discounts"),
        Category(name="Sign Up", embedding_text="Create account", llm_description="User wants to sign up for an account"),
        Category(name="Login", embedding_text="User login", llm_description="User wants to log into their account"),
        Category(name="Logout", embedding_text="User logout", llm_description="User wants to log out of their account")
    ]

def embed(text: str) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding

@trace
def _narrow_down_categories(text: str, categories: list[Category]) -> list[Category]:
    embeddings: list[tuple[Category, list[float]]] = []
    for category in categories:
        embeddings.append((category, embed(category.embedding_text)))
    text_embedding = embed(text)
    best_matches: list[tuple[Category, float]] = []
    for category, embedding in embeddings:
        cosine_similarity = np.dot(text_embedding, embedding) / (np.linalg.norm(text_embedding) * np.linalg.norm(embedding))
        best_matches.append((category, cosine_similarity))
    max_matches = 5
    matches = sorted(best_matches, key=lambda x: x[1], reverse=True)[:max_matches]
    return [match[0] for match in matches]

def _narrow_down_categories_llm(text: str, categories: list[Category]) -> list[Category]:
    tb = TypeBuilder()
    for i, category in enumerate(categories):
        val = tb.Category.add_value(category.name)
        val.alias(f"k{i}")
        val.description(category.llm_description)
    selected_categories = b.PickBestCategories(text, count=3, baml_options={ "tb": tb })
    return [category for category in categories if category.name in selected_categories]


def _pick_best_category(text: str, categories: list[Category]) -> Category:
    tb = TypeBuilder()
    for i, category in enumerate(categories):
        val = tb.Category.add_value(category.name)
        val.alias(f"k{i}")
        val.description(category.llm_description)

    selected_category = b.PickBestCategory(text, { "tb": tb })
    for category in categories:
        if category.name == selected_category:
            return category
    # IMPOSSIBLE TO HAPPEN THANKS TO BAML!
    raise ValueError(f"Selected category {selected_category} not found in categories")

@trace
def pick_category(text: str) -> str:
    use_llm_to_narrow_down_categories = False

    categories = load_categories()
    narrowed_down_categories = _narrow_down_categories(text, categories)
    if use_llm_to_narrow_down_categories:
        narrowed_down_categories_llm = _narrow_down_categories_llm(text, categories)
        narrowed_down_categories = narrowed_down_categories_llm
    category = _pick_best_category(text, narrowed_down_categories)
    return category.name


if __name__ == "__main__":
    print(pick_category("I want to buy a new phone"))