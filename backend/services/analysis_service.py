import sys
import os
import gc

# Add parent directory to path to import analysis.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from analysis import analyze_video_ultrafast, analyze_audio_ultrafast, generate_fast_report
from moviepy.editor import VideoFileClip
import tempfile
import time

class AnalysisService:
    """Service for handling video/audio communication analysis"""
    
    @staticmethod
    def analyze_video(video_path):
        """
        Analyze video for communication skills
        Returns: (results_dict, report_path, error)
        """
        temp_audio_path = None
        video_clip = None
        
        try:
            # Extract audio from video
            audio_results = None
            
            try:
                print("--- 🎵 Extracting audio from video...")
                
                # Create temp file
                temp_audio_file = tempfile.NamedTemporaryFile(
                    suffix='.wav', 
                    delete=False
                )
                temp_audio_path = temp_audio_file.name
                temp_audio_file.close()
                
                # Open video file
                video_clip = VideoFileClip(video_path)
                
                if video_clip.audio:
                    # Write audio
                    video_clip.audio.write_audiofile(
                        temp_audio_path, 
                        verbose=False, 
                        logger=None
                    )
                    
                    # Close audio explicitly
                    video_clip.audio.close()
                    
                    # Close video clip
                    video_clip.close()
                    video_clip = None
                    
                    # Force garbage collection
                    gc.collect()
                    
                    # Wait for file handles to release
                    time.sleep(1)
                    
                    # Analyze audio
                    audio_results = analyze_audio_ultrafast(temp_audio_path)
                else:
                    # No audio in video
                    video_clip.close()
                    video_clip = None
                    gc.collect()
                        
            except Exception as e:
                print(f"Audio extraction warning: {e}")
                # Ensure clip is closed
                if video_clip:
                    try:
                        video_clip.close()
                    except:
                        pass
                video_clip = None
                gc.collect()
            
            # Analyze video
            print("--- 🎥 Analyzing video...")
            video_results = analyze_video_ultrafast(video_path)
            
            # Generate report
            report_filename = f"Analysis_Report_{os.path.basename(video_path).split('.')[0]}.docx"
            report_path = os.path.join(os.path.dirname(video_path), report_filename)
            
            overall_score = generate_fast_report(video_results, audio_results, report_path)
            
            # Prepare response data
            results = {
                'overall_score': overall_score,
                'video_analysis': {
                    'posture_score': video_results.get('posture_score', 0),
                    'eye_contact_score': video_results.get('eye_contact_score', 0),
                    'confidence_score': video_results.get('confidence_score', 0),
                    'frames_analyzed': video_results.get('frames_analyzed', 0)
                },
                'audio_analysis': None
            }
            
            if audio_results:
                results['audio_analysis'] = {
                    'wpm': audio_results.get('wpm', 0),
                    'filler_count': audio_results.get('filler_count', 0),
                    'monotony': audio_results.get('monotony', 'N/A'),
                    'duration': audio_results.get('duration', 0)
                }
            
            return results, report_path, None
            
        except Exception as e:
            return None, None, str(e)
        
        finally:
            # Ensure video clip is closed
            if video_clip:
                try:
                    video_clip.close()
                except:
                    pass
            
            # Force garbage collection again
            gc.collect()
            
            # Clean up temporary audio file with aggressive retry logic
            if temp_audio_path and os.path.exists(temp_audio_path):
                deleted = False
                max_retries = 10
                
                for attempt in range(max_retries):
                    try:
                        time.sleep(0.5)
                        os.remove(temp_audio_path)
                        print(f"✅ Cleaned up temporary audio file")
                        deleted = True
                        break
                    except (PermissionError, OSError) as e:
                        if attempt < max_retries - 1:
                            print(f"⏳ Retrying cleanup (attempt {attempt + 1}/{max_retries})...")
                            gc.collect()  # Force garbage collection
                            time.sleep(1)
                        else:
                            print(f"⚠️ Could not delete temp file after {max_retries} attempts")
                            print(f"   File: {temp_audio_path}")
                            print(f"   This is safe - Windows will clean it up eventually")
                
                # If still couldn't delete, try to schedule for deletion on reboot
                if not deleted:
                    try:
                        # Mark file for deletion on next reboot (Windows only)
                        if os.name == 'nt':
                            import win32api
                            import win32con
                            win32api.MoveFileEx(
                                temp_audio_path, 
                                None, 
                                win32con.MOVEFILE_DELAY_UNTIL_REBOOT
                            )
                            print("   ✓ Scheduled for deletion on reboot")
                    except:
                        pass
    
    @staticmethod
    def get_analysis_summary(results):
        """Generate a text summary from analysis results"""
        summary = []
        
        overall_score = results.get('overall_score', 0)
        summary.append(f"Overall Communication Score: {overall_score}/100")
        
        video = results.get('video_analysis', {})
        if video:
            summary.append(f"\nBody Language:")
            summary.append(f"- Posture: {video.get('posture_score', 0):.1f}%")
            summary.append(f"- Eye Contact: {video.get('eye_contact_score', 0):.1f}%")
            summary.append(f"- Confidence: {video.get('confidence_score', 0):.1f}%")
        
        audio = results.get('audio_analysis')
        if audio:
            summary.append(f"\nVocal Delivery:")
            summary.append(f"- Speaking Pace: {audio.get('wpm', 0):.0f} words per minute")
            summary.append(f"- Filler Words: {audio.get('filler_count', 0)}")
            summary.append(f"- Vocal Variety: {audio.get('monotony', 'N/A')}")
        
        return '\n'.join(summary)