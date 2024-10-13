class Solution:
    def removeElement(self, nums, val):
        """
        :type nums: List[int]
        :type val: int
        :rtype: int
        """
        left = 0
        right = len(nums) - 1

        while left <= right:
            if nums[left] == val:
                nums[left] = nums[right]
                right -= 1
                print(nums)
            else:
                left += 1
                print(nums)

        return left

# Example usage
nums = [0, 1, 2, 2, 3, 0, 4, 2]
val = 2

# Instantiate the Solution class and call the method
solution = Solution()
k = solution.removeElement(nums, val)
print(k)  # Should be 5
print(nums[:k])  # Should be [0, 1, 4, 0, 3], or another combination where order is not guaranteed
