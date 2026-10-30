import { IFlowNodeParameter } from '@/types/flow';
import { convertKeysToCamelCase } from '@/utils/flow';
import { Cascader } from 'antd';

export const renderCascader = (data: IFlowNodeParameter) => {
  const attr = convertKeysToCamelCase(data.ui?.attr || {});

  return <Cascader {...attr} options={data.options} placeholder="请选择" className='w-full nodrag' />;
};
