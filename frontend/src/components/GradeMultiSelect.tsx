import { MultiSelectDropdown } from './MultiSelectDropdown';
import type { MultiSelectOption } from './MultiSelectDropdown';
import type { HadithGrade } from '../types';

interface GradeMultiSelectProps {
  selectedGrades: HadithGrade[];
  onSelectionChange: (grades: HadithGrade[]) => void;
}

const gradeOptions: MultiSelectOption[] = [
  { value: 'sahih', label: 'Sahih' },
  { value: 'hasan-sahih', label: 'Hasan Sahih' },
  { value: 'hasan', label: 'Hasan' },
  { value: 'daif-hasan', label: 'Daif Hasan' },
  { value: 'daif', label: 'Daif' },
];

export const GradeMultiSelect = ({ selectedGrades, onSelectionChange }: GradeMultiSelectProps) => {
  const handleSelectionChange = (values: string[]) => {
    onSelectionChange(values as HadithGrade[]);
  };

  return (
    <MultiSelectDropdown
      label="Filter by Grade"
      options={gradeOptions}
      selectedValues={selectedGrades}
      onSelectionChange={handleSelectionChange}
      placeholder="Select grades"
    />
  );
};
