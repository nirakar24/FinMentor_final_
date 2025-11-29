import PropTypes from 'prop-types';

const SkeletonCard = () => {
  return (
    <div className="card animate-pulse">
      <div className="h-4 bg-slate-200 rounded w-1/3 mb-4"></div>
      <div className="h-8 bg-slate-200 rounded w-2/3 mb-2"></div>
      <div className="h-4 bg-slate-200 rounded w-1/4"></div>
    </div>
  );
};

const SkeletonLoader = ({ count = 4 }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {Array.from({ length: count }).map((_, index) => (
        <SkeletonCard key={index} />
      ))}
    </div>
  );
};

SkeletonLoader.propTypes = {
  count: PropTypes.number,
};

export default SkeletonLoader;
