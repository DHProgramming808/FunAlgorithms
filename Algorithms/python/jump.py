"""
Jump Game

Given an integer array nums, return True if you can reach
the last index starting from the first index.

Each element in nums represents your maximum jump length at that position.
"""

def solve(nums):
    jump_dest = len(nums) - 1

    if jump_dest == 0:
        return True

    while jump_dest > 0:
        possible_jump_origins = []

        for i in range(jump_dest):
            if nums[i] + i >= jump_dest:
                possible_jump_origins.append(i)

        if len(possible_jump_origins) == 0:
            return False

        jump_dest = min(possible_jump_origins)

        if jump_dest == 0:
            return True