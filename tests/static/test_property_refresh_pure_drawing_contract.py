"""Offline contract checks only: no VB compilation, Inventor, Vault or APPLY validation."""
import pathlib
import re
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[2] / 'scripts/ilogic/experiments/BEEXCITED_PropertyRefreshPure.iLogicVb'

def mirror_drawing(existing, filename, target):
    if not re.fullmatch(r'PJ[0-9]{5}', target, flags=re.I):
        raise ValueError('invalid project prefix')
    if not existing or not filename:
        return existing
    pattern = r'^PJ[0-9]{5}-'
    if not re.match(pattern, existing, re.I) or not re.match(pattern, filename, re.I):
        return existing
    if existing[:7].casefold() != filename[:7].casefold():
        return existing
    return target.upper() + existing[7:]

class DrawingContract(unittest.TestCase):
    def test_source_named_contract_and_no_mutation(self):
        source = SOURCE.read_text(encoding='utf-8')
        self.assertRegex(source, r'Public Function PlanExistingDrawingProperty\(ByVal filePath As String, ByVal filenameStem As String, ByVal existingDrawingNumber As String, ByVal targetProjectPrefix As String\) As PropertyChange')
        self.assertIn('PlanDrawingNumber(existingValue:=existingDrawingNumber, fileBaseName:=filenameStem, proposed:=targetProjectPrefix)', source)
        self.assertIn('If String.Equals(existingDrawingNumber, nextValue, StringComparison.Ordinal) Then Return Nothing', source)
        self.assertNotIn('Save2(', source)
        self.assertNotIn('MessageBox.', source)
        self.assertNotIn('InputBox(', source)

    def test_behavioral_mirror_cases(self):
        cases = [
            ('PJ00201-3410-01', 'PJ00201-3410-01', 'PJ00333', 'PJ00333-3410-01'),
            ('pj00201-3410-PJ00201', 'PJ00201-3410', 'pj00333', 'PJ00333-3410-PJ00201'),
            ('PJ00201-3410', 'PJ00999-3410', 'PJ00333', 'PJ00201-3410'),
            ('PJ00201-3410', 'NOT-PROJECT', 'PJ00333', 'PJ00201-3410'),
            ('PJ00201', 'PJ00201', 'PJ00333', 'PJ00201'),
            ('PJ00201X-3410', 'PJ00201X-3410', 'PJ00333', 'PJ00201X-3410'),
            ('PJ00333-3410', 'PJ00333-3410', 'PJ00333', 'PJ00333-3410'),
            ('ABC-PJ00201-3410', 'PJ00201-3410', 'PJ00333', 'ABC-PJ00201-3410'),
            (None, 'PJ00201-3410', 'PJ00333', None),
        ]
        for existing, filename, target, expected in cases:
            with self.subTest(existing=existing, filename=filename):
                self.assertEqual(mirror_drawing(existing, filename, target), expected)

    def test_bad_target_fails(self):
        for target in ('PJ1234', 'PJ123456', 'AB12345', 'PJ12X45'):
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    mirror_drawing('PJ00201-3410', 'PJ00201-3410', target)

if __name__ == '__main__':
    unittest.main()
