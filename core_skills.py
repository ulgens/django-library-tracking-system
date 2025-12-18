import random

numbers = list(range(0, 101))

# Create a list of 10 random numbers between 1 and 20.
rand_list = [random.randrange(0, 20) for _ in range(0,11)]


# Filter Numbers Below 10 (List Comprehension)
list_comprehension_below_10 = [number for number in numbers if number < 10]

# Filter Numbers Below 10 (Using filter)
list_comprehension_below_10_with_filter = list(filter(lambda x: x < 10, numbers))
