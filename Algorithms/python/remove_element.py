"""
Remove Element

Given an integer array nums and an integer val,remove all occurrences of val in nums in-place.

Consider the number of elements in nums which are not equal to val be k, to get accepted, you need to do the following things: Change the array nums such that the first k elements of nums contain the elements which are not equal to val. The remaining elements of nums are not important as well as the size of nums. Return k.
"""

def solve(nums, val):
    k = 0

    last_place = len(nums) - 1
    last_good_val = len(nums) - 1

    while last_place >= 0:
        if nums[last_place] == val:
            k += 1
            if last_place == last_good_val:
                nums[last_place] = 0
            else:
                nums[last_place] = nums[last_good_val]
                nums[last_good_val] = 0
            last_good_val -= 1
        last_place -= 1

    k = len(nums) - k
    return k